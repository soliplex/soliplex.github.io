#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Documentation build script for Soliplex multi-project documentation.

This script copies documentation from git submodules in the projects/ directory
into the docs/ directory for MkDocs to build. It handles:
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


def validate_mkdocs_nav(mkdocs_yml: Path, docs_dir: Path) -> List[str]:
    """Validate that all files referenced in mkdocs.yml navigation exist."""
    print("\n🔍 Validating navigation references...")
    errors = []

    if not mkdocs_yml.exists():
        errors.append(f"mkdocs.yml not found at {mkdocs_yml}")
        return errors

    # Simple validation - check if referenced paths exist
    # This is a basic check; could be expanded to parse YAML properly
    with open(mkdocs_yml, 'r', encoding='utf-8') as f:
        content = f.read()

    # Look for .md file references in the nav section
    import re
    nav_started = False
    for line in content.split('\n'):
        if line.strip().startswith('nav:'):
            nav_started = True
            continue
        if nav_started:
            if line and not line[0].isspace():
                break  # End of nav section

            # Match patterns like "- Something: path/to/file.md"
            match = re.search(r':\s+([a-zA-Z0-9_/-]+\.md)', line)
            if match:
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
    mkdocs_yml = Path('mkdocs.yml')

    # Projects with dedicated docs/ directories
    projects_with_docs = {
        'soliplex': 'projects/soliplex/docs',
        'ingester': 'projects/ingester/docs',
        'chatbot': 'projects/chatbot/docs',
        'flutter': 'projects/flutter/docs',
    }

    # Projects with only README.md
    readme_only_projects = [
        'ingester-agents',
        'pdf-splitter',
    ]

    all_projects = list(projects_with_docs.keys()) + readme_only_projects

    # Validate only mode
    if args.validate_only:
        errors = validate_mkdocs_nav(mkdocs_yml, docs_dir)
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
    nav_errors = validate_mkdocs_nav(mkdocs_yml, docs_dir)

    # Update .gitignore
    generate_gitignore(docs_dir, all_projects)

    # Final status
    print("\n" + "=" * 60)
    if all_errors or nav_errors:
        print("⚠️  Build completed with warnings")
        print("\nTo build documentation, run:")
        print("   mkdocs serve    # For local preview")
        print("   mkdocs build    # For production build")
        return 1
    else:
        print("✅ Documentation build completed successfully!")
        print("\nTo build documentation, run:")
        print("   mkdocs serve    # For local preview")
        print("   mkdocs build    # For production build")
        return 0


if __name__ == '__main__':
    sys.exit(main())
