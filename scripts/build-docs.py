#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Documentation build script for Soliplex multi-project documentation.

This script copies documentation from git submodules in the projects/ directory
into the docs/ directory for Zensical to build. It handles:
- Updating git submodules
- Copying docs/ directories from each project
- Converting README.md to index.md for projects without docs/
- Validating that all referenced files exist
"""

import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Configure stdout for UTF-8 on Windows
if platform.system() == 'Windows':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def update_submodules(skip_update: bool = False) -> bool:
    """Update all git submodules to latest commit."""
    if skip_update:
        print("⏭️  Skipping git submodule update (--no-update flag)")
        return True

    print("📥 Updating git submodules...")
    try:
        result = subprocess.run(
            ['git', 'submodule', 'update', '--init', '--recursive', '--remote'],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Submodules updated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to update submodules: {e.stderr}")
        return False


def clean_docs_directory(docs_dir: Path, projects: List[str]) -> None:
    """Remove existing project directories from docs/."""
    print("\n🧹 Cleaning existing project documentation...")
    for project in projects:
        dest = docs_dir / project
        if dest.exists() and dest.is_dir():
            shutil.rmtree(dest)
            print(f"   Removed docs/{project}/")


def copy_project_docs(
    projects_with_docs: Dict[str, str],
    docs_dir: Path
) -> Tuple[int, List[str]]:
    """Copy docs/ directories from projects to main docs/."""
    print("\n📚 Copying documentation from projects...")
    copied = 0
    errors = []

    for name, source_path in projects_with_docs.items():
        src = Path(source_path)
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
    readme_projects: List[str],
    docs_dir: Path
) -> Tuple[int, List[str]]:
    """Copy README.md as index.md for projects without docs/ directory."""
    print("\n📄 Copying README.md files for projects without docs/...")
    copied = 0
    errors = []

    for project in readme_projects:
        readme = Path(f'projects/{project}/README.md')
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


def validate_nav(config_file: Path, docs_dir: Path) -> List[str]:
    """Validate that all files referenced in navigation exist."""
    print("\n🔍 Validating navigation references...")
    errors = []

    if not config_file.exists():
        errors.append(f"Config file not found at {config_file}")
        return errors

    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()

    import re
    for match in re.finditer(r'=\s*"([a-zA-Z0-9_/-]+\.md)"', content):
        file_path = docs_dir / match.group(1)
        if not file_path.exists():
            errors.append(f"Referenced file not found: {match.group(1)}")

    if errors:
        print(f"   ⚠️  Found {len(errors)} broken references")
    else:
        print("   ✓ All navigation references valid")

    return errors


def generate_gitignore(docs_dir: Path, projects: List[str]) -> None:
    """Generate or update .gitignore to exclude copied project docs."""
    gitignore_path = docs_dir / '.gitignore'

    # Read existing .gitignore if it exists
    existing_lines = set()
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
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


def discover_projects(projects_root: Path) -> Tuple[Dict[str, str], List[str]]:
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
    import argparse

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
        help='Only validate navigation, do not copy files'
    )
    args = parser.parse_args()

    print("=" * 60)
    print("🚀 Soliplex Documentation Build Script")
    print("=" * 60)

    # Configuration
    docs_dir = Path('docs')
    config_file = Path('zensical.toml')
    projects_root = Path('projects')

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
        errors = validate_nav(config_file, docs_dir)
        if errors:
            print("\n❌ Validation failed:")
            for error in errors:
                print(f"   - {error}")
            return 1
        print("\n✅ Validation passed!")
        return 0

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

    # Validate navigation
    nav_errors = validate_nav(config_file, docs_dir)

    # Update .gitignore
    generate_gitignore(docs_dir, all_projects)

    # Final status
    print("\n" + "=" * 60)
    if all_errors or nav_errors:
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
