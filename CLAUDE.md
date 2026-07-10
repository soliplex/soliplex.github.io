# Claude Context: Soliplex Multi-Project Documentation System

This document provides context for Claude (or any AI assistant) to understand and modify this documentation system.

## Project Overview

This is a **unified documentation site** (`soliplex.github.io`) that aggregates documentation from **7 separate git submodule repositories** and builds it with [Zensical](https://github.com/squidfunk/zensical). When documentation changes in any submodule, the site automatically rebuilds and deploys.

### Core Concept

```
Individual Repos          Documentation Site
┌─────────────┐          ┌──────────────────┐
│  soliplex   │──────┐   │ soliplex.github  │
│  /docs      │      │   │      .io         │
└─────────────┘      │   │                  │
┌─────────────┐      ├──>│  Aggregates all  │
│  ingester   │      │   │  documentation   │
│  /docs      │──────┤   │  into one site   │
└─────────────┘      │   │                  │
┌─────────────┐      │   └──────────────────┘
│  chatbot    │──────┤            │
│  /docs      │      │            ▼
└─────────────┘      │   https://soliplex.github.io/
     (+ 4 more)──────┘
```

## Prerequisites

### Python Environment

**Required**: This project uses [uv](https://github.com/astral-sh/uv) for Python package management.

- **Python Version**: 3.13 or higher
- **Package Manager**: uv (required for running build scripts)

**Installation**:

```bash
# Install uv (see https://github.com/astral-sh/uv for platform-specific instructions)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
# OR
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Verify installation
uv --version
```

**Why uv?**
- Fast dependency resolution and installation
- Reproducible builds via lock files
- No need to manually manage virtual environments
- Commands like `uv run python script.py` automatically handle dependencies

## Architecture

### 1. Git Submodules

Location: `projects/` directory

Each submodule is a separate git repository:
- `projects/soliplex/` - Core platform docs
- `projects/ingester/` - Document ingestion system
- `projects/chatbot-widget/` - Chat widget (repo: soliplex/chatbot; served at /chatbot-widget/ to avoid the repo's own /chatbot/ Pages site)
- `projects/frontend/` - Flutter client
- `projects/ingester-agents/` - Ingestion agents (README only)
- `projects/pdf-splitter/` - PDF utilities (README only)
- `projects/bubble-sandbox/` - Bubble sandbox (README only)

**Key File**: `.gitmodules` - Defines all submodules

### 2. Documentation Build System

**Main Script**: `scripts/build-docs.py`

This Python script:
1. Copies `docs/` directories from each submodule to `docs/<project-name>/`
2. Converts `README.md` to `index.md` for projects without docs/
3. Generates `zensical.toml` from `zensical.toml.template`, expanding each `@auto:<project>` nav stub from the copied docs tree and recording submodule commit hashes in a `[doc_sources]` table
4. Validates the generated navigation (broken references **and** orphaned pages)
5. Updates `.gitignore` to ignore copied files

**Important**: Both the copied `docs/<project>/` files and the generated `zensical.toml` are NOT committed to git - they're produced on each build. Only `zensical.toml.template` is tracked.

### 3. Automated Triggers

**Workflow**: `.github/workflows/build-docs.yml`

Triggers on:
- `push` to main branch (manual changes to this repo)
- `schedule` (nightly `cron: 0 6 * * *`) to pick up upstream submodule changes
- `repository_dispatch` with type `docs_update` (automatic from submodules)
- `workflow_dispatch` (manual trigger via GitHub UI)

**Process**:
```
1. Checkout repo with submodules
2. uv sync (install deps + dev tools)
3. ruff check . (lint gate)
4. Run build-docs.py (updates submodules, copies docs, generates zensical.toml)
5. zensical build
6. Deploy site/ to GitHub Pages (gh-pages branch) via ghp-import
```

### 4. Submodule Triggers

**Template**: `.github/workflows/TRIGGER_TEMPLATES/submodule-trigger-template.yml`

Each submodule has a workflow that:
- Triggers on push to main when **markdown files** change
- Path filters: `docs/**/*.md`, `docs/**/*.mdx`, `README.md`
- Sends `repository_dispatch` event to `soliplex.github.io`
- Uses organization secret `DOCS_DEPLOY_TOKEN`
- Uses `jq` to properly escape JSON payload

**Current Status**: 6 submodules have trigger workflows in PRs

## Key Files Reference

### Configuration

| File | Purpose | When to Edit |
|------|---------|--------------|
| `zensical.toml.template` | Site config, theme & nav structure (incl. `@auto:` stubs and `[nav_title_overrides]`) | Add/remove projects, change nav structure or titles |
| `zensical.toml` | **Generated** from the template — do not edit | Never (git-ignored, regenerated each build) |
| `.gitmodules` | Git submodule definitions | Add/remove submodule repositories |
| `docs/index.md` | Landing page content | Update project descriptions |
| `scripts/build-docs.py` | Build/generation logic | Change copy, nav-generation, or validation behavior |

### Documentation

| File | Purpose |
|------|---------|
| `DOCUMENTATION_BUILD.md` | Build system guide for users |
| `SUBMODULE_TRIGGER_METHODS.md` | Analysis of trigger methods |
| `SETUP_COMPLETE.md` | Setup status and PR links |
| `JSON_PAYLOAD_FIX.md` | Fix for JSON escaping issue |
| `TROUBLESHOOTING_DISPATCH.md` | Debug guide for triggers |

### Workflows

| File | Purpose |
|------|---------|
| `.github/workflows/build-docs.yml` | Main build & deploy workflow |
| `.github/workflows/TRIGGER_TEMPLATES/submodule-trigger-template.yml` | Template for submodule triggers |
| `.github/workflows/README.md` | Workflow documentation |

## Common Tasks

### Adding a New Project

`build-docs.py` auto-discovers any submodule under `projects/`, so there is no project list to edit — adding a project is mostly a navigation change.

1. **Add as git submodule**:
   ```bash
   git submodule add https://github.com/soliplex/new-project.git projects/new-project
   git commit -m "chore: add new-project submodule"
   ```

2. **Add a nav stub to `zensical.toml.template`**:
   ```toml
   { "New Project" = "@auto:new-project" },
   ```
   Optionally add `[nav_title_overrides]` entries to tune page/section titles.

3. **Update `docs/index.md`**:
   - Add section describing the new project
   - Add to "Documentation Updates" list

4. **Add trigger workflow to new-project repo**:
   - Copy `.github/workflows/TRIGGER_TEMPLATES/submodule-trigger-template.yml`
   - Create PR in new-project repository
   - Ensure organization secret `DOCS_DEPLOY_TOKEN` has access

5. **Test**:
   ```bash
   uv run python scripts/build-docs.py --no-update
   uv run zensical serve
   ```

### Removing a Project

1. **Remove the `@auto:` stub (and any overrides) from `zensical.toml.template`**
2. **Remove from `docs/index.md`**
3. **Remove git submodule**:
   ```bash
   git submodule deinit -f projects/project-name
   git rm -f projects/project-name
   rm -rf .git/modules/projects/project-name
   git commit -m "docs: remove project-name from documentation"
   ```

### Updating Navigation Structure

**File**: `zensical.toml.template` (the generated `zensical.toml` is never edited by hand)

Curate the section structure and local pages here; each subrepo section is an
`@auto:<project>` stub that `build-docs.py` expands from the copied docs tree.
All paths are relative to the `docs/` directory:
```toml
nav = [
  { "Home" = "index.md" },                  # literal local page
  { "Core Platform" = "@auto:soliplex" },   # auto-expanded from docs/soliplex/
  { "User Interfaces" = [
    { "Chatbot Widget" = "@auto:chatbot-widget" },
    { "Flutter UI" = "@auto:frontend" },
  ]},
]

# Optional title overrides, keyed by relative doc path or directory:
[nav_title_overrides]
"soliplex/config/oidc_providers.md" = "OIDC Authentication"
```

**Important**:
- Use forward slashes `/` even on Windows
- Generated nav entries use `.md` files (`.mdx` is copied but not added to nav)
- Paths are case-sensitive
- The `[nav_title_overrides]` table is stripped from the generated `zensical.toml`

### Modifying Path Filters

**Template**: `.github/workflows/TRIGGER_TEMPLATES/submodule-trigger-template.yml`

Current filters (markdown only):
```yaml
paths:
  - 'docs/**/*.md'
  - 'docs/**/*.mdx'
  - 'README.md'
  - '.github/workflows/trigger-docs-deploy.yml'
```

To change what triggers builds, modify the `paths` section.

### Testing Locally

```bash
# 1. Install dependencies (deps + dev tools)
uv sync

# 2. Update submodules, copy docs, and generate zensical.toml
uv run python scripts/build-docs.py

# 3. Validate only (regenerate config + check nav, no copying)
uv run python scripts/build-docs.py --validate-only

# 4. Serve locally (http://127.0.0.1:9001/)
uv run zensical serve

# 5. Build production (outputs to site/)
uv run zensical build
```

## File Paths & Patterns

### Source Files (in submodules)
```
projects/
├── soliplex/docs/          # Full docs directory
│   ├── overview.md
│   ├── config/
│   │   ├── installation.md
│   │   └── ...
├── ingester/docs/          # Full docs directory
├── ingester-agents/        # README only
│   └── README.md
```

### Generated Files (gitignored)
```
docs/
├── index.md                # Committed (landing page)
├── img/                    # Committed (shared assets)
├── soliplex/               # Generated - gitignored
│   ├── overview.md
│   └── config/
├── ingester/               # Generated - gitignored
├── ingester-agents/        # Generated - gitignored
│   └── index.md            # Copied from README.md
└── .gitignore              # Auto-updated by build-docs.py
```

## Important Constraints

### 1. Workflow Must Be on Main Branch

`repository_dispatch` events **only trigger workflows on the default branch**.

If you modify `.github/workflows/build-docs.yml`, **commit to main** for it to work.

### 2. JSON Payload Must Be Escaped

The trigger workflow uses `jq` to escape JSON. **Never** use direct string interpolation:

❌ **WRONG**:
```yaml
-d '{"message": "${{ github.event.head_commit.message }}"}'
```

✅ **CORRECT**:
```yaml
payload=$(jq -n --arg message "${{ github.event.head_commit.message }}" ...)
-d "$payload"
```

### 3. Organization Secret Required

The trigger workflow requires:
- **Name**: `DOCS_DEPLOY_TOKEN`
- **Type**: Personal Access Token (PAT)
- **Scope**: `public_repo` or `repo`
- **Access**: All submodule repositories

### 4. Path Filters Are Case-Sensitive

```yaml
paths:
  - 'docs/**/*.md'   # Matches docs/file.md
  - 'docs/**/*.MD'   # Does NOT match docs/file.md
```

### 5. Submodule Updates Required

Before building, always update submodules:
```bash
git submodule update --init --recursive --remote
```

Or use the build script which does this automatically (unless `--no-update` is specified).

## Current Configuration

### Projects: 7 Total

| Project | Type | Docs Location | In Nav |
|---------|------|---------------|--------|
| soliplex | Full docs | `projects/soliplex/docs/` | ✅ |
| ingester | Full docs | `projects/ingester/docs/` | ✅ |
| chatbot | Full docs | `projects/chatbot-widget/docs/` | ✅ |
| frontend | Full docs | `projects/frontend/docs/` | ✅ |
| ingester-agents | README only | `projects/ingester-agents/README.md` | ✅ |
| pdf-splitter | README only | `projects/pdf-splitter/README.md` | ✅ |
| bubble-sandbox | README only | `projects/bubble-sandbox/README.md` | ✅ |

### Trigger Status

| Repository | Branch | PR Status | Trigger Active |
|------------|--------|-----------|----------------|
| soliplex | `docs/add-rebuild-trigger` | Pending | ❌ |
| ingester | `docs/add-rebuild-trigger` | Pending | ❌ |
| chatbot | `docs/add-rebuild-trigger` | Pending | ❌ |
| frontend | `docs/add-rebuild-trigger` | Pending | ❌ |
| ingester-agents | `docs/add-rebuild-trigger` | Pending | ❌ |
| pdf-splitter | `docs/add-rebuild-trigger` | Pending | ❌ |
| bubble-sandbox | `docs/add-rebuild-trigger` | Pending | ❌ |

**Status**: Workflows created, PRs need to be merged.

### Branch Configuration

- **Main repo branch**: `main`
- **Submodule branches**: Varies (main or master)
- **GitHub Pages source**: `gh-pages` branch (auto-generated)
- **Deploy target**: https://soliplex.github.io/

## Debugging

### Build Fails

1. **Check validation**:
   ```bash
   uv run python scripts/build-docs.py --validate-only
   ```

2. **Common issues**:
   - A `[nav_title_overrides]` key in `zensical.toml.template` points at a path that no longer exists (broken reference)
   - A new upstream page the generated nav now includes (orphan — usually expected)
   - Incorrect file paths (case-sensitive)
   - Submodules not updated

### Trigger Not Working

1. **Verify workflow is on main branch**:
   ```bash
   git checkout main
   ls .github/workflows/build-docs.yml
   ```

2. **Check for `repository_dispatch` trigger**:
   ```bash
   grep -A 2 "repository_dispatch" .github/workflows/build-docs.yml
   ```

3. **Verify organization secret access**:
   - Go to: https://github.com/orgs/soliplex/settings/secrets/actions
   - Check `DOCS_DEPLOY_TOKEN` has access to submodule repos

4. **Check submodule workflow logs**:
   - Look for HTTP 204 response (success)
   - Look for HTTP 400/401 (authentication or JSON error)

### Pages Not Updating

1. **Check both workflows ran**:
   - "Build and Deploy Docs" workflow
   - "pages-build-deployment" workflow (automatic)

2. **Verify gh-pages branch was updated**:
   ```bash
   git fetch origin
   git log origin/gh-pages
   ```

3. **Check GitHub Pages settings**:
   - Repository Settings → Pages
   - Source should be: `gh-pages` branch
   - Custom domain (if any) should be configured

## Performance

### Build Times

Typical build: 1-2 minutes total
- Submodule update: 30 seconds
- Documentation copy + config generation: 20-30 seconds
- Zensical build: a few seconds
- GitHub Pages deploy (ghp-import): 10-20 seconds
- Pages build: 30-60 seconds

### GitHub Actions Costs

Free tier: 2,000 minutes/month
- Per documentation update: ~3-5 minutes
- Can handle: ~400-600 updates/month
- That's ~13-20 updates per day

## Security Notes

- Organization secret used for cross-repo triggers
- Token should have minimal permissions (`public_repo` only)
- Rotate token every 90 days
- Trigger only on markdown changes (path filters prevent code execution)
- All workflows run in GitHub's isolated environments

## Zensical Theme

This site is built with Zensical (a Material-style theme). All theme settings live
in `zensical.toml.template` (copied verbatim into the generated `zensical.toml`).

**Theme Features Enabled**:
- Code annotations, copy, select
- Navigation tabs (sticky)
- Instant loading with prefetch
- Search with suggestions
- Table of contents follows scroll

**Custom Configuration**:
- Logo: `img/logo.png`
- Color palette with light/dark/system toggle
- Dev server address: `127.0.0.1:9001`

## Quick Reference Commands

```bash
# Update all submodules to latest
git submodule update --remote

# Build documentation locally
uv run python scripts/build-docs.py && uv run zensical serve

# Validate navigation only
uv run python scripts/build-docs.py --validate-only

# Build for production
uv run python scripts/build-docs.py && uv run zensical build

# Lint (same gate as CI)
uv run ruff check .

# Add new submodule
git submodule add URL projects/name

# Remove submodule
git submodule deinit -f projects/name
git rm -f projects/name
```

## Links

- **Live Site**: https://soliplex.github.io/
- **Repository**: https://github.com/soliplex/soliplex.github.io
- **Actions**: https://github.com/soliplex/soliplex.github.io/actions
- **Organization Secrets**: https://github.com/orgs/soliplex/settings/secrets/actions

---

**Last Updated**: 2026-06-01
**Documentation Version**: Zensical build with template-generated navigation and repository_dispatch + nightly triggers
**Active Projects**: 7 (soliplex, ingester, chatbot, frontend, ingester-agents, pdf-splitter, bubble-sandbox)
