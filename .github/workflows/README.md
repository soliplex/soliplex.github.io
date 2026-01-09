# GitHub Actions Workflow Documentation

## Build and Deploy Docs Workflow

This workflow automatically builds and deploys the Soliplex documentation site to GitHub Pages.

### Trigger Events

- **Push to main branch**: Automatically rebuilds and deploys documentation
- **Manual trigger**: Can be manually triggered via `workflow_dispatch`

### Workflow Steps

#### 1. Checkout with Submodules
```yaml
- uses: actions/checkout@v6
  with:
    submodules: recursive
    fetch-depth: 0
```

**Critical**: The `submodules: recursive` option ensures all git submodules in the `projects/` directory are checked out. Without this, the documentation from individual projects won't be available.

#### 2. Update Submodules to Latest
```yaml
- name: Update submodules to latest
  run: git submodule update --init --recursive --remote
```

This pulls the latest documentation from each submodule repository, ensuring the documentation is always up-to-date.

#### 3. Setup Python and Dependencies
```yaml
- uses: actions/setup-python@v6
  with:
    python-version: '3.x'

- name: Install dependencies
  run: pip install mkdocs-material
```

Installs Python and the Material for MkDocs theme.

#### 4. Build Documentation from Submodules
```yaml
- name: Build documentation from submodules
  run: python scripts/build-docs.py --no-update
```

**Critical Step**: Runs the `build-docs.py` script to copy documentation from all submodules into the `docs/` directory. This step is essential because:

- Copies docs from projects with `docs/` directories (soliplex, ingester, ag-ui, chatbot, flutter)
- Converts README.md to index.md for projects without docs/ (ingester-agents, pdf-splitter)
- Validates all navigation references
- Updates `.gitignore` for copied files

The `--no-update` flag is used because we already updated submodules in step 2.

#### 5. Deploy to GitHub Pages
```yaml
- name: Deploy to GitHub Pages
  run: mkdocs gh-deploy --force
```

Builds the MkDocs site and deploys it to the `gh-pages` branch.

#### 6. Slack Notification on Failure
Sends a notification to the `#soliplex` Slack channel if the deployment fails.

### Required Secrets

- `SLACK_NOTIFY_URL`: Webhook URL for Slack notifications (optional)

### Required Permissions

```yaml
permissions:
  contents: write      # To push to gh-pages branch
  pages: write         # To deploy to GitHub Pages
  id-token: write      # For GitHub Pages deployment
```

## What Was Fixed

### Previous Issues

1. **Missing Submodule Checkout**: The workflow checked out the main repository but didn't initialize submodules, so documentation from `projects/*/` was missing.

2. **No Documentation Build Step**: The workflow went directly from installing dependencies to deploying, skipping the critical step of copying documentation from submodules using `build-docs.py`.

3. **Outdated Submodules**: Even if submodules existed, they weren't being updated to the latest version.

### Current Solution

The workflow now:
1. ✅ Checks out all submodules recursively
2. ✅ Updates submodules to latest commits
3. ✅ Runs `build-docs.py` to copy all documentation
4. ✅ Validates navigation references automatically
5. ✅ Deploys the complete, unified documentation site

## Testing the Workflow

### Test Locally

Before pushing, test the build process locally:

```bash
# Update submodules
git submodule update --init --recursive --remote

# Run build script
python scripts/build-docs.py --no-update

# Test MkDocs build
mkdocs build

# Preview locally
mkdocs serve
```

### Monitor Deployment

1. Push to main branch
2. Go to Actions tab: https://github.com/soliplex/soliplex.github.io/actions
3. Watch the "Build and Deploy Docs" workflow
4. Check deployment at: https://soliplex.github.io/

## Troubleshooting

### Submodule Update Failures

If submodules fail to update, check:
- Repository access permissions
- Submodule URLs in `.gitmodules`
- Branch references in submodules

### Build Script Failures

If `build-docs.py` fails:
- Check that all projects in the script configuration exist
- Verify file paths match what's in the submodules
- Check script output for specific error messages

### MkDocs Build Failures

If MkDocs build fails:
- Check for broken navigation references in `mkdocs.yml`
- Verify all referenced files exist after build script runs
- Check MkDocs Material theme is installed

## Manual Deployment

To manually trigger deployment:

1. Go to Actions tab
2. Select "Build and Deploy Docs" workflow
3. Click "Run workflow"
4. Select branch (main)
5. Click "Run workflow"

---

**Last Updated**: 2026-01-09
