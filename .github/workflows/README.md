# GitHub Actions Workflow Documentation

## Build and Deploy Docs Workflow

[`build-docs.yml`](build-docs.yml) builds the Soliplex documentation site with
[Zensical](https://github.com/squidfunk/zensical) and deploys it to the
`gh-pages` branch.

### Trigger Events

- **Push to `main`**: rebuilds and deploys
- **Schedule**: nightly (`cron: 0 6 * * *`) to pick up upstream submodule changes
- **`repository_dispatch` (`docs_update`)**: sent by submodule repos when their docs change (see [`TRIGGER_TEMPLATES/`](TRIGGER_TEMPLATES/))
- **Manual**: via `workflow_dispatch` in the Actions UI

### Workflow Steps

#### 1. Checkout with submodules

```yaml
- uses: actions/checkout@v6
  with:
    submodules: recursive
    fetch-depth: 0
```

Ensures all git submodules in `projects/` are available; without this the
per-project documentation is missing.

#### 2. Set up Python and uv

```yaml
- uses: actions/setup-python@v6
  with:
    python-version: '3.13'
- uses: astral-sh/setup-uv@v7
- name: Install dependencies
  run: uv sync
```

`uv sync` installs the project plus the dev dependency group (including `ruff`).

#### 3. Lint

```yaml
- name: Lint
  run: uv run ruff check .
```

A lint failure blocks the build.

#### 4. Build docs (copy + generate config)

```yaml
- name: Run build-docs.py
  run: uv run python scripts/build-docs.py
```

Updates submodules to their latest commits, copies each project's docs into
`docs/<project>/`, generates `zensical.toml` from `zensical.toml.template`
(expanding `@auto:` nav stubs), and validates the navigation. (No `--no-update`
flag — the script performs the submodule update itself.)

#### 5. Build the site

```yaml
- name: Build site
  run: uv run zensical build
```

Renders the static site into `site/`.

#### 6. Deploy to GitHub Pages

```yaml
- name: Deploy to GitHub Pages
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    uv run ghp-import -n -p -f site
```

Publishes `site/` to the `gh-pages` branch with `ghp-import`.

#### 7. Slack notification on failure

Posts to the `#soliplex` Slack channel if the run fails.

### Required Secrets

- `SLACK_NOTIFY_URL`: Webhook URL for failure notifications (optional)

### Required Permissions

```yaml
permissions:
  contents: write      # To push to gh-pages branch
  pages: write         # GitHub Pages
  id-token: write      # GitHub Pages deployment
```

## Submodule Trigger Template

[`TRIGGER_TEMPLATES/submodule-trigger-template.yml`](TRIGGER_TEMPLATES/) is
copied into each submodule repository. When that repo pushes documentation
changes, it sends a `repository_dispatch` (`docs_update`) event here using the
`DOCS_DEPLOY_TOKEN` secret, triggering an immediate rebuild.

## Testing the Workflow

Before pushing, test the build locally:

```bash
uv sync
uv run ruff check .
uv run python scripts/build-docs.py --no-update
uv run zensical build
uv run zensical serve   # Preview at http://127.0.0.1:9001/
```

## Troubleshooting

### Submodule update failures

Check repository access permissions, submodule URLs in `.gitmodules`, and the
branch references in each submodule.

### Build script failures

Run `uv run python scripts/build-docs.py --validate-only` to see broken
navigation references or orphaned pages.

### Zensical build failures

Verify that referenced files exist after the build script runs, and check the
upstream markdown for errors. Navigation structure lives in
`zensical.toml.template`, not in the generated `zensical.toml`.

## Manual Deployment

1. Go to the Actions tab
2. Select the "Build and Deploy Documentation" workflow
3. Click "Run workflow" → select `main` → "Run workflow"
