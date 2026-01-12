# Multi-Project Documentation Build Guide

This document explains how the Soliplex multi-project documentation system works and how to use it.

## Overview

The Soliplex documentation site aggregates documentation from multiple git submodules located in the `projects/` directory. Each submodule is a separate repository that can be updated independently.

## Architecture

### Directory Structure

```
soliplex.github.io/
├── docs/                          # Main docs directory for MkDocs
│   ├── index.md                   # Main landing page
│   ├── img/                       # Shared images
│   ├── soliplex/                  # Copied from projects/soliplex/docs/
│   ├── ingester/                  # Copied from projects/ingester/docs/
│   ├── ag-ui/                     # Copied from projects/ag-ui/docs/
│   ├── chatbot/                   # Copied from projects/chatbot/docs/
│   ├── flutter/                   # Copied from projects/flutter/docs/
│   ├── ingester-agents/           # Created from projects/ingester-agents/README.md
│   ├── pdf-splitter/              # Created from projects/pdf-splitter/README.md
│   └── .gitignore                 # Ignores copied project directories
├── projects/                      # Git submodules (not tracked in main repo)
│   ├── soliplex/
│   ├── ingester/
│   ├── ag-ui/
│   ├── chatbot/
│   ├── flutter/
│   ├── ingester-agents/
│   └── pdf-splitter/
├── scripts/
│   ├── build-docs.py              # Main build script
│   └── compare-methods.py         # Comparison tool for different approaches
└── mkdocs.yml                     # MkDocs configuration

```

### How It Works

The documentation uses **Method 3: Copy Files with Build Script** approach:

1. **Git Submodules**: Each project is a git submodule in `projects/`
2. **Build Script**: `scripts/build-docs.py` copies documentation files from submodules to `docs/`
3. **MkDocs Build**: MkDocs builds the site from the unified `docs/` directory
4. **Gitignore**: Copied files are gitignored to avoid duplication

## Usage

### Prerequisites

- Python 3.12+
- Git
- uv (Python package manager) or pip

### Initial Setup

1. Clone the repository with submodules:
   ```bash
   git clone --recursive https://github.com/soliplex/soliplex.github.io.git
   cd soliplex.github.io
   ```

2. If you already cloned without `--recursive`, initialize submodules:
   ```bash
   git submodule update --init --recursive
   ```

### Building Documentation

#### Step 1: Update Submodules (Optional)

To get the latest documentation from all projects:

```bash
git submodule update --remote
```

Or use the build script with automatic updating:

```bash
uv run scripts/build-docs.py
```

#### Step 2: Copy Documentation Files

To copy documentation without updating submodules:

```bash
uv run scripts/build-docs.py --no-update
```

The script will:
- Clean existing project directories in `docs/`
- Copy all documentation from submodules
- Convert README.md to index.md for projects without docs/
- Validate all navigation references
- Update `.gitignore`

#### Step 3: Build the Site

For local preview:

```bash
mkdocs serve
```

Visit http://127.0.0.1:8001 to view the documentation.

For production build:

```bash
mkdocs build
```

This creates the static site in the `site/` directory.

### Validation Only

To validate navigation without copying files:

```bash
uv run scripts/build-docs.py --validate-only --no-update
```

## Script Options

### build-docs.py

```bash
uv run scripts/build-docs.py [OPTIONS]
```

Options:
- `--no-update`: Skip git submodule update
- `--validate-only`: Only validate navigation, don't copy files
- `-h, --help`: Show help message

### compare-methods.py

Compare different approaches for multi-project documentation:

```bash
uv run scripts/compare-methods.py
```

This analyzes your system and recommends the best method for your setup.

## Workflow

### Regular Documentation Updates

When documentation in a submodule project changes:

1. Update the specific submodule:
   ```bash
   cd projects/soliplex
   git pull origin main
   cd ../..
   ```

2. Run the build script:
   ```bash
   uv run scripts/build-docs.py --no-update
   ```

3. Preview changes:
   ```bash
   mkdocs serve
   ```

4. Commit the submodule update to the main repo:
   ```bash
   git add projects/soliplex
   git commit -m "docs: update soliplex documentation"
   ```

### Adding a New Project

1. Add the project as a submodule:
   ```bash
   git submodule add https://github.com/soliplex/new-project.git projects/new-project
   ```

2. Update `scripts/build-docs.py`:
   - Add to `projects_with_docs` if it has a `docs/` directory
   - Add to `readme_only_projects` if it only has a `README.md`

3. Update `mkdocs.yml` navigation to include the new project

4. Update `docs/index.md` to reference the new project

5. Run the build script and test:
   ```bash
   uv run scripts/build-docs.py
   mkdocs serve
   ```

## CI/CD Integration

For automated builds (GitHub Actions, etc.):

```yaml
- name: Update submodules
  run: git submodule update --init --recursive --remote

- name: Build documentation
  run: |
    pip install mkdocs mkdocs-material
    python scripts/build-docs.py --no-update
    mkdocs build

- name: Deploy
  # Your deployment steps here
```

## Troubleshooting

### Broken Links

If you see "Referenced file not found" errors:

1. Check which files are missing:
   ```bash
   uv run scripts/build-docs.py --validate-only --no-update
   ```

2. Verify the files exist in the source submodule:
   ```bash
   ls projects/PROJECT_NAME/docs/
   ```

3. Update `mkdocs.yml` to reference the correct paths

### Submodule Update Issues

If submodules won't update:

```bash
# Reset to tracking branch
git submodule update --remote --merge

# Or force update
git submodule foreach git pull origin main
```

### Unicode Errors on Windows

The scripts handle UTF-8 encoding automatically. If you still see encoding errors, ensure your terminal supports UTF-8:

```powershell
# PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

## Project Configuration

### Files That Must Remain Stable

Each project submodule must have:
- `README.md` (guaranteed to exist)
- Optional: `docs/` directory with markdown files

The build script handles both cases automatically.

### Supported File Types

- `.md` - Standard Markdown
- `.mdx` - MDX format (Material for MkDocs supports this)

## Alternative Methods

The current implementation uses **Method 3 (Copy Files)**. Other methods were evaluated:

1. **Symlinks**: Not cross-platform compatible (Windows issues)
2. **MkDocs Monorepo Plugin**: Requires additional plugin and configuration

See `scripts/compare-methods.py` for detailed comparison.

## Maintenance

### Updating the Build Script

The build script is located at `scripts/build-docs.py`. Key sections:

- `projects_with_docs`: Dict of projects with `docs/` directories
- `readme_only_projects`: List of projects with only README.md
- `validate_mkdocs_nav()`: Validates navigation references

### Updating Navigation

Edit `mkdocs.yml` to change the site navigation structure. All paths are relative to the `docs/` directory.

## Best Practices

1. **Always run the build script before deploying** to ensure all documentation is current
2. **Validate after changes** using `--validate-only` flag
3. **Keep navigation in sync** with available documentation files
4. **Document new projects** in `docs/index.md` for discoverability
5. **Update submodules periodically** to keep documentation fresh

## Getting Help

- Issues with the build script: Check `scripts/build-docs.py` logs
- Issues with MkDocs: See [MkDocs documentation](https://www.mkdocs.org/)
- Issues with submodules: See [Git Submodules documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)

---

**Last Updated**: 2026-01-09
