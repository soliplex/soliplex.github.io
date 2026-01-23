# Claude Context: Soliplex Multi-Project Documentation System

This document provides context for Claude (or any AI assistant) to understand and modify this documentation system.

## Project Overview

This is a **unified documentation site** (`soliplex.github.io`) that aggregates documentation from **6 separate git submodule repositories**. When documentation changes in any submodule, the site automatically rebuilds and deploys.

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
     (+ 3 more)──────┘
```

## Prerequisites

### Python Environment

**Required**: This project uses [uv](https://github.com/astral-sh/uv) for Python package management.

- **Python Version**: 3.12 or higher
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
- `projects/chatbot/` - Chat widget
- `projects/flutter/` - Flutter client
- `projects/ingester-agents/` - Ingestion agents (README only)
- `projects/pdf-splitter/` - PDF utilities (README only)

**Key File**: `.gitmodules` - Defines all submodules

### 2. Documentation Build System

**Main Script**: `scripts/build-docs.py`

This Python script:
1. Copies `docs/` directories from each submodule to `docs/<project-name>/`
2. Converts `README.md` to `index.md` for projects without docs/
3. Validates all navigation references in `mkdocs.yml`
4. Updates `.gitignore` to ignore copied files

**Important**: Copied files are NOT committed to git - they're generated on each build.

### 3. Automated Triggers

**Workflow**: `.github/workflows/build-docs.yml`

Triggers on:
- `push` to main branch (manual changes to this repo)
- `workflow_dispatch` (manual trigger via GitHub UI)
- `repository_dispatch` with type `docs_update` (automatic from submodules)

**Process**:
```
1. Checkout repo with submodules
2. Update submodules to latest
3. Run build-docs.py to copy documentation
4. Run mkdocs build
5. Deploy to GitHub Pages (gh-pages branch)
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
| `mkdocs.yml` | Site navigation & theme | Add/remove projects, change nav structure |
| `.gitmodules` | Git submodule definitions | Add/remove submodule repositories |
| `docs/index.md` | Landing page content | Update project descriptions |
| `scripts/build-docs.py` | Build script configuration | Add/remove projects from build |

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

1. **Add as git submodule**:
   ```bash
   git submodule add https://github.com/soliplex/new-project.git projects/new-project
   git commit -m "chore: add new-project submodule"
   ```

2. **Update `scripts/build-docs.py`**:
   ```python
   # If project has docs/ directory:
   projects_with_docs = {
       # ... existing projects
       'new-project': 'projects/new-project/docs',
   }

   # If project has only README.md:
   readme_only_projects = [
       # ... existing projects
       'new-project',
   ]
   ```

3. **Update `mkdocs.yml` navigation**:
   ```yaml
   nav:
     - Supporting Tools:
         - New Project: new-project/index.md
   ```

4. **Update `docs/index.md`**:
   - Add section describing the new project
   - Add to "Documentation Updates" list

5. **Add trigger workflow to new-project repo**:
   - Copy `.github/workflows/TRIGGER_TEMPLATES/submodule-trigger-template.yml`
   - Create PR in new-project repository
   - Ensure organization secret `DOCS_DEPLOY_TOKEN` has access

6. **Test**:
   ```bash
   uv run python scripts/build-docs.py --no-update
   uv run mkdocs serve
   ```

### Removing a Project

1. **Remove from `mkdocs.yml` navigation**
2. **Remove from `docs/index.md`**
3. **Remove from `scripts/build-docs.py`** project lists
4. **Remove git submodule**:
   ```bash
   git submodule deinit -f projects/project-name
   git rm -f projects/project-name
   rm -rf .git/modules/projects/project-name
   git commit -m "docs: remove project-name from documentation"
   ```

### Updating Navigation Structure

**File**: `mkdocs.yml`

All paths are relative to `docs/` directory:
```yaml
nav:
  - Section Name:
      - Page Title: project-name/file-name.md
      - Subsection:
          - Page: project-name/subfolder/file.md
```

**Important**:
- Use forward slashes `/` even on Windows
- File extensions must be `.md` (not `.mdx`)
- Paths are case-sensitive

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
# 1. Update submodules
git submodule update --init --recursive --remote

# 2. Run build script
python scripts/build-docs.py --no-update

# 3. Validate only (no file copying)
python scripts/build-docs.py --validate-only --no-update

# 4. Serve locally
mkdocs serve

# 5. Build production
mkdocs build
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

### Projects: 6 Total

| Project | Type | Docs Location | In MkDocs |
|---------|------|---------------|-----------|
| soliplex | Full docs | `projects/soliplex/docs/` | ✅ |
| ingester | Full docs | `projects/ingester/docs/` | ✅ |
| chatbot | Full docs | `projects/chatbot/docs/` | ✅ |
| flutter | Full docs | `projects/flutter/docs/` | ✅ |
| ingester-agents | README only | `projects/ingester-agents/README.md` | ✅ |
| pdf-splitter | README only | `projects/pdf-splitter/README.md` | ✅ |

### Trigger Status

| Repository | Branch | PR Status | Trigger Active |
|------------|--------|-----------|----------------|
| soliplex | `docs/add-rebuild-trigger` | Pending | ❌ |
| ingester | `docs/add-rebuild-trigger` | Pending | ❌ |
| chatbot | `docs/add-rebuild-trigger` | Pending | ❌ |
| flutter | `docs/add-rebuild-trigger` | Pending | ❌ |
| ingester-agents | `docs/add-rebuild-trigger` | Pending | ❌ |
| pdf-splitter | `docs/add-rebuild-trigger` | Pending | ❌ |

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
   python scripts/build-docs.py --validate-only --no-update
   ```

2. **Common issues**:
   - Broken navigation references in `mkdocs.yml`
   - Missing files referenced in navigation
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

Typical build: 2-3 minutes total
- Submodule update: 30 seconds
- Documentation copy: 20-30 seconds
- MkDocs build: 30-60 seconds
- GitHub Pages deploy: 10-20 seconds
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

## MkDocs Material Theme

This site uses Material for MkDocs with customizations:

**Theme Features Enabled**:
- Code annotations, copy, select
- Navigation tabs (sticky)
- Instant loading with prefetch
- Search with suggestions
- Table of contents follows scroll

**Custom Configuration**:
- Logo: `img/logo.png`
- Color scheme: Deep purple primary, amber accent
- Dark/light mode toggle
- Dev server port: 8001

## Quick Reference Commands

```bash
# Update all submodules to latest
git submodule update --remote

# Build documentation locally
python scripts/build-docs.py && mkdocs serve

# Validate navigation only
python scripts/build-docs.py --validate-only --no-update

# Build for production
python scripts/build-docs.py && mkdocs build

# Compare documentation methods
python scripts/compare-methods.py

# Test repository_dispatch event
export GITHUB_TOKEN=your_token
./test-dispatch.sh

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

**Last Updated**: 2026-01-09
**Documentation Version**: Multi-project automated system with repository_dispatch triggers
**Active Projects**: 6 (soliplex, ingester, chatbot, flutter, ingester-agents, pdf-splitter)
