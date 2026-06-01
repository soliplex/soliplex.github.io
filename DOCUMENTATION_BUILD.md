# Multi-Project Documentation Build Guide

This document explains how the Soliplex multi-project documentation system works and how to use it.

## Overview

The Soliplex documentation site aggregates documentation from multiple git submodules located in the `projects/` directory. Each submodule is a separate repository that can be updated independently. The site is built with [Zensical](https://github.com/squidfunk/zensical).

## Architecture

### Directory Structure

```text
soliplex.github.io/
├── docs/                          # Site content directory for Zensical
│   ├── index.md                   # Landing page (tracked)
│   ├── img/                       # Shared images (tracked)
│   ├── soliplex/                  # Copied from projects/soliplex/docs/
│   ├── ingester/                  # Copied from projects/ingester/docs/
│   ├── chatbot/                   # Copied from projects/chatbot/docs/
│   ├── frontend/                  # Copied from projects/frontend/docs/
│   ├── ingester-agents/           # Created from projects/ingester-agents/README.md
│   ├── pdf-splitter/              # Created from projects/pdf-splitter/README.md
│   ├── bubble-sandbox/            # Created from projects/bubble-sandbox/README.md
│   └── .gitignore                 # Ignores copied project directories
├── projects/                      # Git submodules (upstream sources)
├── scripts/
│   └── build-docs.py              # Copy docs + generate zensical.toml + validate nav
├── zensical.toml.template         # Source of truth: site config + nav stubs (tracked)
├── zensical.toml                  # Generated from the template (git-ignored)
└── pyproject.toml                 # Dependencies, ruff & pymarkdown config
```

### How It Works

1. **Git Submodules**: Each project is a git submodule in `projects/`.
2. **Copy step**: `scripts/build-docs.py` copies each submodule's `docs/` directory (or, for README-only projects, its `README.md` as `index.md`) into `docs/<project>/`.
3. **Config generation**: the same script generates `zensical.toml` from `zensical.toml.template`. Each `@auto:<project>` stub in the template's nav is expanded by walking the copied docs tree, so new/renamed/removed upstream pages appear automatically. The current submodule commit hashes are recorded in a `[doc_sources]` table for provenance.
4. **Validation**: the script validates the generated nav — failing the build on broken references *or* orphaned pages (copied files that no nav entry points to).
5. **Build**: `zensical build` renders the static site into `site/`.

Copied `docs/<project>/` directories and the generated `zensical.toml` are git-ignored; only `docs/index.md`, shared assets, and `zensical.toml.template` are tracked.

## Usage

### Prerequisites

- Python 3.13+
- Git
- [uv](https://github.com/astral-sh/uv) (Python package manager)

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

3. Install dependencies (including dev tools):

   ```bash
   uv sync
   ```

### Building Documentation

To update submodules, copy docs, and generate `zensical.toml`:

```bash
uv run python scripts/build-docs.py
```

To do the same **without** pulling new submodule commits:

```bash
uv run python scripts/build-docs.py --no-update
```

The script will:

- Update submodules (unless `--no-update`)
- Clean and re-copy each project's docs into `docs/`
- Generate `zensical.toml` from `zensical.toml.template`
- Validate the navigation (broken references and orphaned pages)

Then preview or build the site:

```bash
uv run zensical serve    # Preview at http://127.0.0.1:9001/
uv run zensical build    # Production build into site/
```

### Validation Only

To regenerate the config and validate navigation without re-copying files:

```bash
uv run python scripts/build-docs.py --validate-only
```

## Script Options

### build-docs.py

```bash
uv run python scripts/build-docs.py [OPTIONS]
```

Options:

- `--no-update`: Skip the `git submodule update`
- `--validate-only`: Generate the config and validate navigation; do not copy files
- `-h, --help`: Show help message

## Workflow

### Regular Documentation Updates

Upstream documentation changes flow in automatically — the deploy workflow runs nightly and on a `repository_dispatch` from each submodule repo. To roll an update in manually:

1. Update the submodule pointer:

   ```bash
   cd projects/soliplex
   git pull origin main
   cd ../..
   ```

2. Rebuild locally and preview:

   ```bash
   uv run python scripts/build-docs.py --no-update
   uv run zensical serve
   ```

3. Commit the submodule update:

   ```bash
   git add projects/soliplex
   git commit -m "docs: update soliplex documentation"
   ```

### Adding a New Project

`build-docs.py` auto-discovers any submodule under `projects/` (a `docs/` directory makes it a full-docs project; otherwise its `README.md` becomes `index.md`), so adding a project is mostly a navigation change:

1. Add the project as a submodule:

   ```bash
   git submodule add https://github.com/soliplex/new-project.git projects/new-project
   ```

2. Add an `@auto:new-project` nav stub to `zensical.toml.template` (and any `[nav_title_overrides]` you want).

3. Run the build and confirm the nav validates:

   ```bash
   uv run python scripts/build-docs.py
   ```

## CI/CD Integration

Deployment is handled by [`.github/workflows/build-docs.yml`](.github/workflows/build-docs.yml), which on each run:

1. Checks out the repo with submodules
2. Installs dependencies with `uv sync`
3. Lints with `ruff check .`
4. Runs `scripts/build-docs.py`
5. Builds the site with `zensical build`
6. Publishes `site/` to the `gh-pages` branch with `ghp-import`

It triggers on push to `main`, a nightly schedule, `repository_dispatch` (`docs_update`), and manual dispatch.

## Troubleshooting

### Broken Links / Missing Pages

If the build reports "Referenced file not found" or "Orphaned page not in navigation":

1. See exactly what is wrong:

   ```bash
   uv run python scripts/build-docs.py --validate-only
   ```

2. Verify the files exist in the source submodule:

   ```bash
   ls projects/PROJECT_NAME/docs/
   ```

3. A broken reference usually means a `[nav_title_overrides]` key in `zensical.toml.template` points at a path that no longer exists; an orphan means a new upstream page that the auto-generated nav now includes (no action needed) — or a stale manual entry.

### Submodule Update Issues

If submodules won't update:

```bash
# Reset to tracking branch
git submodule update --remote --merge

# Or force update
git submodule foreach git pull origin main
```

### Unicode Errors on Windows

The script handles UTF-8 encoding automatically. If you still see encoding errors, ensure your terminal supports UTF-8:

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

- `.md` — Standard Markdown (emitted into the navigation)
- `.mdx` — MDX format (copied, but not added to the generated nav)

## Alternative Methods

The current implementation uses **Method 3 (Copy Files)**. Other methods were evaluated:

1. **Symlinks**: Not cross-platform compatible (Windows issues)
2. **MkDocs Monorepo Plugin**: Requires additional plugin and configuration

## Maintenance

### Updating the Build Script

The build script is located at `scripts/build-docs.py`. Key pieces:

- `discover_projects()`: Auto-detects projects under `projects/` and classifies them as full-docs vs README-only
- `generate_config()`: Generates `zensical.toml` from the template, expanding `@auto:` nav stubs
- `validate_nav()`: Validates navigation — broken references and orphaned pages

### Updating Navigation

Edit `zensical.toml.template`. Curate section structure and titles there; the per-project page lists are generated from the copied docs. All paths are relative to the `docs/` directory.

## Best Practices

1. **Always run the build script before deploying** to ensure documentation and the generated config are current
2. **Validate after changes** using the `--validate-only` flag
3. **Never edit copied docs or `zensical.toml` by hand** — edit upstream sources or `zensical.toml.template`
