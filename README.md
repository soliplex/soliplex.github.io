# Soliplex Documentation

[![Deploy Docs](https://github.com/soliplex/soliplex.github.io/actions/workflows/build-docs.yml/badge.svg)](https://github.com/soliplex/soliplex.github.io/actions/workflows/build-docs.yml)

Unified documentation site for the Soliplex ecosystem, built with [Zensical](https://github.com/squidfunk/zensical).

**Live site:** <https://soliplex.github.io/>

## Overview

This repository aggregates documentation from several upstream repositories, included here as **git submodules** under `projects/`:

- **[soliplex/soliplex](https://github.com/soliplex/soliplex)** — Core Platform
- **[soliplex/ingester](https://github.com/soliplex/ingester)** — Document Ingestion
- **[soliplex/chatbot](https://github.com/soliplex/chatbot)** — Chatbot Widget
- **[soliplex/frontend](https://github.com/soliplex/frontend)** — Flutter Client
- **[soliplex/ingester-agents](https://github.com/soliplex/ingester-agents)** — Ingester Agents (README only)
- **[soliplex/pdf-splitter](https://github.com/soliplex/pdf-splitter)** — PDF Splitter (README only)
- **[soliplex/bubble-sandbox](https://github.com/soliplex/bubble-sandbox)** — Bubble Sandbox (README only)

## How It Works

1. Each project is a git submodule in `projects/`.
2. `scripts/build-docs.py` copies each submodule's `docs/` (or its `README.md`) into `docs/<project>/`.
3. The same script generates `zensical.toml` from `zensical.toml.template`, expanding each `@auto:<project>` navigation stub by walking the copied docs tree — so new, renamed, or removed upstream pages flow into the site automatically.
4. `zensical build` renders the static site into `site/`.
5. The [build-docs.yml](.github/workflows/build-docs.yml) workflow deploys `site/` to the `gh-pages` branch via `ghp-import`.

The copied `docs/<project>/` directories and the generated `zensical.toml` are git-ignored build artifacts — only `docs/index.md`, shared assets, and `zensical.toml.template` are tracked.

### Rebuild triggers

The deploy workflow runs on:

- **Push** to `main`
- **Nightly** schedule (`cron: 0 6 * * *`) to pick up upstream submodule changes
- **`repository_dispatch`** (`docs_update`) sent by submodule repos when their docs change (see `.github/workflows/TRIGGER_TEMPLATES/`)
- **Manual** dispatch via the GitHub Actions UI

## Development

Requires Python 3.13+ and [uv](https://github.com/astral-sh/uv).

```bash
# Install dependencies (including dev tools like ruff)
uv sync

# Pull the latest docs and generate zensical.toml from the template
uv run python scripts/build-docs.py

# ...or generate/validate without updating submodules
uv run python scripts/build-docs.py --no-update

# Preview locally (http://127.0.0.1:9001/)
uv run zensical serve

# Production build (outputs to site/)
uv run zensical build
```

### Project Structure

```text
soliplex.github.io/
├── .github/workflows/
│   ├── build-docs.yml          # Build & deploy to GitHub Pages
│   └── TRIGGER_TEMPLATES/      # Per-submodule repository_dispatch trigger
├── projects/                   # Git submodules (upstream sources)
├── scripts/
│   └── build-docs.py           # Copy docs + generate zensical.toml + validate nav
├── docs/
│   ├── index.md                # Landing page (tracked)
│   ├── img/                    # Shared assets (tracked)
│   └── <project>/              # Copied from submodules (git-ignored)
├── zensical.toml.template      # Source of truth for site config + nav (tracked)
├── zensical.toml               # Generated from the template (git-ignored)
└── pyproject.toml              # Dependencies, ruff & pymarkdown config
```

### Adding a New Project

1. Add the repository as a submodule under `projects/` and commit the `.gitmodules` change.
2. Add an `@auto:<project>` nav stub (and any title overrides) to `zensical.toml.template`.
3. Add a trigger workflow to the new repo from `.github/workflows/TRIGGER_TEMPLATES/`.
4. Run `uv run python scripts/build-docs.py --no-update` and confirm the nav validates.

## Troubleshooting

### Build Issues

1. Check the [Build Docs workflow runs](https://github.com/soliplex/soliplex.github.io/actions/workflows/build-docs.yml).
2. Run `uv run python scripts/build-docs.py --validate-only` — it reports broken nav references **and** orphaned pages (copied but not in the nav).
3. Check for Markdown errors in the upstream docs.

### Local Development

```bash
# Clean build artifacts
rm -rf site/ .cache/ zensical.toml

# Reinstall dependencies and rebuild
uv sync
uv run python scripts/build-docs.py
uv run zensical serve
```

## Contributing

**Do not edit the copied `docs/<project>/` directories or `zensical.toml` directly** — both are regenerated on every build. To change:

- **Upstream documentation**: edit it in the source repository; it syncs on the next build (nightly, on dispatch, or manually).
- **Site config / navigation structure**: edit `zensical.toml.template`.
- **Landing page**: edit `docs/index.md`.

## License

Documentation is licensed under the same terms as the respective upstream projects.
