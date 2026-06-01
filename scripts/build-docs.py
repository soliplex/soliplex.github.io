#!/usr/bin/env python3
"""
Documentation build script for Soliplex multi-project documentation.

This script copies documentation from git submodules in the projects/ directory
into the docs/ directory for Zensical to build. It handles:
- Updating git submodules
- Copying docs/ directories from each project
- Converting README.md to index.md for projects without docs/
- Generating zensical.toml from zensical.toml.template, expanding per-project
  navigation stubs from the copied docs tree
- Validating that the generated navigation is self-consistent
"""

import argparse
import io
import json
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tomllib

# Configure stdout for UTF-8 on Windows
if platform.system() == 'Windows':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Words that should stay upper-cased when humanizing a file/directory name into a
# navigation title (e.g. "API.md" -> "API", not "Api").
ACRONYMS = {
    'AG', 'AGUI', 'AI', 'API', 'CLI', 'CRUD', 'DB', 'HTTP', 'ID', 'JSON', 'LLM',
    'MCP', 'OAUTH', 'OIDC', 'PDF', 'RAG', 'SQL', 'SSE', 'TUI', 'UI', 'URI',
    'URIS', 'UX', 'YAML',
}

# Candidate landing-page filenames for a directory, in priority order.
INDEX_NAMES = ('index.md', 'README.md', 'readme.md', 'Readme.md')

# A nav value of "@auto:<project>" in the template is expanded from docs/<project>/.
AUTO_PREFIX = '@auto:'

# Everything from this sentinel comment to EOF is build-docs-only config and is
# stripped out of the generated zensical.toml.
SETTINGS_SENTINEL = '# >>> build-docs settings'

# Matches the `nav = [ ... ]` array in the template (closing ']' at column 0).
NAV_RE = re.compile(r'(?ms)^nav = \[.*?^\]')

# A nav node is a single-key mapping {title: value}; value is a path string or a
# list of further nav nodes.
NavValue = str | list["NavNode"]
NavNode = dict[str, NavValue]


def update_submodules(skip_update: bool = False) -> bool:
    """Update all git submodules to latest commit."""
    if skip_update:
        print("⏭️  Skipping git submodule update (--no-update flag)")
        return True

    print("📥 Updating git submodules...")
    try:
        subprocess.run(
            ['git', 'submodule', 'update', '--init', '--recursive', '--remote'],
            capture_output=True,
            text=True,
            check=True,
        )
        print("✅ Submodules updated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to update submodules: {e.stderr}")
        return False


def clean_docs_directory(docs_dir: pathlib.Path, projects: list[str]) -> None:
    """Remove existing project directories from docs/."""
    print("\n🧹 Cleaning existing project documentation...")
    for project in projects:
        dest = docs_dir / project
        if dest.exists() and dest.is_dir():
            shutil.rmtree(dest)
            print(f"   Removed docs/{project}/")


def copy_project_docs(
    projects_with_docs: dict[str, str],
    docs_dir: pathlib.Path,
) -> tuple[int, list[str]]:
    """Copy docs/ directories from projects to main docs/."""
    print("\n📚 Copying documentation from projects...")
    copied = 0
    errors = []

    for name, source_path in projects_with_docs.items():
        src = pathlib.Path(source_path)
        if not src.exists():
            errors.append(f"Source directory not found: {source_path}")
            continue

        dest = docs_dir / name
        try:
            shutil.copytree(src, dest)
            file_count = len(list(dest.rglob('*.md'))) + len(list(dest.rglob('*.mdx')))
            print(f"   ✓ {name:20s} → docs/{name}/ ({file_count} files)")
            copied += 1
        except Exception as e:
            errors.append(f"Failed to copy {source_path}: {e}")

    return copied, errors


def copy_readme_only_projects(
    readme_projects: list[str],
    docs_dir: pathlib.Path,
) -> tuple[int, list[str]]:
    """Copy README.md as index.md for projects without docs/ directory."""
    print("\n📄 Copying README.md files for projects without docs/...")
    copied = 0
    errors = []

    for project in readme_projects:
        readme = pathlib.Path(f'projects/{project}/README.md')
        if not readme.exists():
            errors.append(f"README.md not found for project: {project}")
            continue

        dest_dir = docs_dir / project
        dest_dir.mkdir(exist_ok=True)
        try:
            shutil.copy(readme, dest_dir / 'index.md')
            print(f"   ✓ {project:20s} → docs/{project}/index.md")
            copied += 1
        except Exception as e:
            errors.append(f"Failed to copy README for {project}: {e}")

    return copied, errors


# --------------------------------------------------------------------------
# Navigation generation
# --------------------------------------------------------------------------
def _humanize(name: str) -> str:
    """Turn a file/directory base name into a human-readable nav title.

    Splits on underscores, hyphens and spaces; keeps known acronyms upper-cased
    and Title-cases everything else. E.g. ``GETTING_STARTED`` -> "Getting
    Started", ``API`` -> "API", ``developer-setup`` -> "Developer Setup".
    """
    words = []
    for part in re.split(r'[_\-\s]+', name.strip()):
        if not part:
            continue
        if part.upper() in ACRONYMS:
            words.append(part.upper())
        else:
            words.append(part[:1].upper() + part[1:].lower())
    return ' '.join(words) or name


def _title_for(rel: str, fallback_name: str, overrides: dict[str, str]) -> str:
    """Title for a page/section: explicit override wins, else humanized name."""
    if rel in overrides:
        return overrides[rel]
    return _humanize(fallback_name)


def build_dir_nodes(
    dir_path: pathlib.Path,
    docs_dir: pathlib.Path,
    overrides: dict[str, str],
) -> list[NavNode]:
    """Build nav nodes for the entries directly under ``dir_path``.

    Order: the directory's landing page first (titled "Overview" unless
    overridden), then leaf pages, then sub-sections — each group sorted by title.
    """
    nodes: list[NavNode] = []

    index = next((dir_path / n for n in INDEX_NAMES if (dir_path / n).exists()), None)
    if index is not None:
        rel = index.relative_to(docs_dir).as_posix()
        nodes.append({overrides.get(rel, 'Overview'): rel})

    files = []
    subdirs = []
    for child in sorted(dir_path.iterdir(), key=lambda p: p.name.lower()):
        if index is not None and child == index:
            continue
        if child.is_dir():
            subdirs.append(child)
        elif child.suffix == '.md':
            files.append(child)

    leaf_nodes: list[NavNode] = []
    for f in files:
        rel = f.relative_to(docs_dir).as_posix()
        leaf_nodes.append({_title_for(rel, f.stem, overrides): rel})
    leaf_nodes.sort(key=lambda n: next(iter(n)).lower())

    dir_nodes: list[NavNode] = []
    for d in subdirs:
        value = build_dir_value(d, docs_dir, overrides)
        if value is None:
            continue
        reldir = d.relative_to(docs_dir).as_posix()
        dir_nodes.append({overrides.get(reldir, _humanize(d.name)): value})
    dir_nodes.sort(key=lambda n: next(iter(n)).lower())

    return nodes + leaf_nodes + dir_nodes


def build_dir_value(
    dir_path: pathlib.Path,
    docs_dir: pathlib.Path,
    overrides: dict[str, str],
) -> NavValue | None:
    """Nav value for a directory: a list of nodes, or a single page collapsed to a
    direct path string, or None when the directory has no markdown."""
    nodes = build_dir_nodes(dir_path, docs_dir, overrides)
    if not nodes:
        return None
    if len(nodes) == 1:
        only_value = next(iter(nodes[0].values()))
        if isinstance(only_value, str):
            return only_value
    return nodes


def build_project_value(
    project_dir: pathlib.Path,
    docs_dir: pathlib.Path,
    overrides: dict[str, str],
) -> NavValue | None:
    """Nav value for a whole project's copied docs directory."""
    if not project_dir.is_dir():
        return None
    return build_dir_value(project_dir, docs_dir, overrides)


def expand_nav(
    nodes: list[NavNode],
    docs_dir: pathlib.Path,
    overrides: dict[str, str],
    errors: list[str],
) -> list[NavNode]:
    """Recursively replace ``@auto:<project>`` stubs with generated nav subtrees."""
    expanded: list[NavNode] = []
    for node in nodes:
        (title, value), = node.items()
        if isinstance(value, str) and value.startswith(AUTO_PREFIX):
            project = value[len(AUTO_PREFIX):]
            generated = build_project_value(docs_dir / project, docs_dir, overrides)
            if not generated:
                errors.append(
                    f"Auto-nav stub '{value}' produced no pages "
                    f"(is docs/{project}/ present with markdown?)"
                )
                continue
            expanded.append({title: generated})
        elif isinstance(value, list):
            expanded.append({title: expand_nav(value, docs_dir, overrides, errors)})
        else:
            expanded.append({title: value})
    return expanded


def _toml_str(value: str) -> str:
    """Quote a string as a TOML basic string (JSON escaping is compatible)."""
    return json.dumps(value, ensure_ascii=False)


def dump_nav_value(value: NavValue, indent: int = 0) -> str:
    """Serialize an expanded nav value back to TOML in the inline-table style."""
    if isinstance(value, str):
        return _toml_str(value)

    pad = '  ' * indent
    child_pad = '  ' * (indent + 1)
    lines = ['[']
    for node in value:
        (title, val), = node.items()
        lines.append(
            f'{child_pad}{{ {_toml_str(title)} = {dump_nav_value(val, indent + 1)} }},'
        )
    lines.append(f'{pad}]')
    return '\n'.join(lines)


def get_submodule_hashes(projects: list[str]) -> dict[str, str]:
    """Return each project's currently checked-out submodule commit hash."""
    hashes: dict[str, str] = {}
    for project in projects:
        try:
            result = subprocess.run(
                ['git', '-C', f'projects/{project}', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                check=True,
            )
            hashes[project] = result.stdout.strip()
        except subprocess.CalledProcessError:
            hashes[project] = 'unknown'
    return hashes


def render_provenance(hashes: dict[str, str]) -> str:
    """Render the do-not-edit banner + a ``[doc_sources]`` table recording the
    upstream submodule commit each project's docs were generated from.

    zensical ignores this unknown top-level table, so it serves as machine-readable
    provenance in the deployed config.
    """
    lines = [
        "# This file is GENERATED by scripts/build-docs.py from",
        "# zensical.toml.template — DO NOT EDIT BY HAND.",
        "",
        "# Upstream submodule commit each project's docs were generated from.",
        "[doc_sources]",
    ]
    for project in sorted(hashes):
        lines.append(f'{project} = {_toml_str(hashes[project])}')
    return '\n'.join(lines) + '\n\n'


def generate_config(
    template_file: pathlib.Path,
    config_file: pathlib.Path,
    docs_dir: pathlib.Path,
    projects: list[str],
) -> list[str]:
    """Generate zensical.toml from the template, expanding per-project nav stubs."""
    print("\n🧭 Generating navigation from template...")
    errors: list[str] = []

    if not template_file.exists():
        errors.append(f"Template not found: {template_file}")
        return errors

    # Short-circuit: if the existing config's [doc_sources] manifest already matches
    # the current submodule hashes, the copied docs (and thus the generated nav) are
    # identical, so there is nothing to regenerate. We still regenerate when the
    # template is newer than the config, since its structure/overrides may have
    # changed without any submodule moving.
    current_hashes = get_submodule_hashes(projects)
    if config_file.exists():
        try:
            existing = tomllib.loads(config_file.read_text(encoding='utf-8'))
        except tomllib.TOMLDecodeError:
            existing = {}
        template_unchanged = template_file.stat().st_mtime <= config_file.stat().st_mtime
        if existing.get('doc_sources') == current_hashes and template_unchanged:
            print("   ✓ Submodule hashes unchanged — keeping existing zensical.toml")
            return errors

    template_text = template_file.read_text(encoding='utf-8')
    data = tomllib.loads(template_text)
    overrides = data.get('nav_title_overrides', {})
    nav = data.get('project', {}).get('nav')
    if nav is None:
        errors.append("Template has no [project].nav array")
        return errors

    expanded = expand_nav(nav, docs_dir, overrides, errors)
    nav_text = 'nav = ' + dump_nav_value(expanded, 0)

    body, count = NAV_RE.subn(lambda _m: nav_text, template_text, count=1)
    if count == 0:
        errors.append("Could not locate 'nav = [ ... ]' block in template")
        return errors

    # Drop the build-docs-only settings block (overrides table) from the output.
    body = body.split(SETTINGS_SENTINEL, 1)[0].rstrip() + '\n'

    provenance = render_provenance(current_hashes)
    config_file.write_text(provenance + body, encoding='utf-8')

    page_count = len(re.findall(r'= "[^"]+\.md"', nav_text))
    print(f"   ✓ Wrote {config_file} ({page_count} pages in navigation)")
    return errors


def validate_nav(
    config_file: pathlib.Path,
    docs_dir: pathlib.Path,
    projects: list[str],
) -> list[str]:
    """Validate navigation references against the copied documentation.

    Reports two kinds of problems, both of which fail the build:
    - Broken references: a file named in the nav does not exist on disk.
    - Orphaned pages: a copied project .md file that no nav entry
      references, so it would silently never appear on the site (this is
      how structural changes in upstream repos get lost).
    """
    print("\n🔍 Validating navigation references...")
    errors = []

    if not config_file.exists():
        errors.append(f"Config file not found at {config_file}")
        return errors

    with open(config_file, encoding='utf-8') as f:
        content = f.read()

    referenced = {
        match.group(1)
        for match in re.finditer(r'=\s*"([a-zA-Z0-9_/-]+\.md)"', content)
    }

    # Broken references: nav points at a file that isn't there.
    for ref in sorted(referenced):
        if not (docs_dir / ref).exists():
            errors.append(f"Referenced file not found: {ref}")

    # Orphaned pages: copied project docs that no nav entry references.
    for project in projects:
        project_dir = docs_dir / project
        if not project_dir.is_dir():
            continue
        for md_file in sorted(project_dir.rglob('*.md')):
            rel = md_file.relative_to(docs_dir).as_posix()
            if rel not in referenced:
                errors.append(f"Orphaned page not in navigation: {rel}")

    if errors:
        print("\n❌ Navigation validation failed:")
        print(f"   ⚠️  Found {len(errors)} navigation problems")
        for error in errors:
            print(f"      - {error}")
    else:
        print("\n✅ Navigation validation passed!")
        print("   ✓ All navigation references valid")

    return errors


def generate_gitignore(docs_dir: pathlib.Path, projects: list[str]) -> None:
    """Generate or update .gitignore to exclude copied project docs."""
    gitignore_path = docs_dir / '.gitignore'

    # Read existing .gitignore if it exists
    existing_lines = set()
    if gitignore_path.exists():
        with open(gitignore_path) as f:
            existing_lines = set(line.strip() for line in f if line.strip())

    # Add project directories
    new_lines = set()
    for project in projects:
        new_lines.add(f"{project}/")

    # Combine and sort
    all_lines = sorted(existing_lines | new_lines)

    # Write back
    with open(gitignore_path, 'w') as f:
        f.write("# Auto-generated by build-docs.py\n")
        f.write("# These directories are copied from git submodules\n\n")
        for line in all_lines:
            f.write(f"{line}\n")

    print(f"\n📝 Updated {gitignore_path}")


def discover_projects(projects_root: pathlib.Path) -> tuple[dict[str, str], list[str]]:
    """
    Automatically discover projects and categorize them.

    Returns:
        Tuple of (projects_with_docs, readme_only_projects)
    """
    projects_with_docs = {}
    readme_only_projects = []

    if not projects_root.exists():
        return projects_with_docs, readme_only_projects

    for project_dir in sorted(projects_root.iterdir()):
        if not project_dir.is_dir():
            continue

        # Skip hidden directories and special directories
        if project_dir.name.startswith('.') or project_dir.name == '__pycache__':
            continue

        project_name = project_dir.name
        docs_path = project_dir / 'docs'
        readme_path = project_dir / 'README.md'

        # Check if project has a docs/ directory with content
        if docs_path.exists() and docs_path.is_dir():
            # Verify it has at least one markdown file
            md_files = list(docs_path.rglob('*.md'))
            if md_files:
                projects_with_docs[project_name] = str(docs_path)
                continue

        # Otherwise, check if it has a README.md
        if readme_path.exists():
            readme_only_projects.append(project_name)

    return projects_with_docs, readme_only_projects


def main():
    """Main entry point for the documentation build script."""

    parser = argparse.ArgumentParser(
        description='Build Soliplex multi-project documentation'
    )
    parser.add_argument(
        '--no-update',
        action='store_true',
        help='Skip git submodule update'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Regenerate the config and validate navigation, do not copy files'
    )
    args = parser.parse_args()

    print("=" * 60)
    print("🚀 Soliplex Documentation Build Script")
    print("=" * 60)

    # Configuration
    docs_dir = pathlib.Path('docs')
    template_file = pathlib.Path('zensical.toml.template')
    config_file = pathlib.Path('zensical.toml')
    projects_root = pathlib.Path('projects')

    # Auto-discover projects
    print("\n🔍 Discovering projects...")
    projects_with_docs, readme_only_projects = discover_projects(projects_root)

    if projects_with_docs:
        print(f"   Found {len(projects_with_docs)} projects with docs/:")
        for name in projects_with_docs.keys():
            print(f"      - {name}")

    if readme_only_projects:
        print(f"   Found {len(readme_only_projects)} README-only projects:")
        for name in readme_only_projects:
            print(f"      - {name}")

    all_projects = list(projects_with_docs.keys()) + readme_only_projects

    # Validate only mode
    if args.validate_only:
        errors = generate_config(template_file, config_file, docs_dir, all_projects)
        errors += validate_nav(config_file, docs_dir, all_projects)
        return 1 if errors else 0

    # Update submodules
    if not update_submodules(args.no_update):
        return 1

    # Clean existing directories
    clean_docs_directory(docs_dir, all_projects)

    # Copy documentation
    copied_docs, doc_errors = copy_project_docs(projects_with_docs, docs_dir)
    copied_readmes, readme_errors = copy_readme_only_projects(
        readme_only_projects,
        docs_dir
    )

    # Report results
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"✓ Projects with docs copied: {copied_docs}/{len(projects_with_docs)}")
    print(f"✓ README-only projects copied: {copied_readmes}/{len(readme_only_projects)}")

    # Report errors
    all_errors = doc_errors + readme_errors
    if all_errors:
        print(f"\n⚠️  Encountered {len(all_errors)} errors:")
        for error in all_errors:
            print(f"   - {error}")

    # Generate zensical.toml from the template (expanding nav stubs)
    gen_errors = generate_config(template_file, config_file, docs_dir, all_projects)

    # Validate navigation (self-consistency check of the generated config)
    nav_errors = validate_nav(config_file, docs_dir, all_projects)

    # Update .gitignore
    generate_gitignore(docs_dir, all_projects)

    # Final status
    print("\n" + "=" * 60)
    if all_errors or gen_errors or nav_errors:
        print("⚠️  Build completed with warnings")
        print("\nTo build documentation, run:")
        print("   zensical serve    # For local preview")
        print("   zensical build    # For production build")
        return 1
    else:
        print("✅ Documentation build completed successfully!")
        print("\nTo build documentation, run:")
        print("   zensical serve    # For local preview")
        print("   zensical build    # For production build")
        return 0


if __name__ == '__main__':
    sys.exit(main())
