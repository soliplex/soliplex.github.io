# Soliplex Documentation

[![Deploy Docs](https://github.com/soliplex/soliplex.github.io/actions/workflows/build-docs.yml/badge.svg)](https://github.com/soliplex/soliplex.github.io/actions/workflows/build-docs.yml)
[![Sync Docs](https://github.com/soliplex/soliplex.github.io/actions/workflows/sync-docs.yml/badge.svg)](https://github.com/soliplex/soliplex.github.io/actions/workflows/sync-docs.yml)

Unified documentation site for the Soliplex ecosystem, built with MkDocs Material.

**Live site:** https://soliplex.github.io/

## Overview

This repository hosts the unified documentation for all Soliplex projects. Documentation is automatically synchronized from multiple upstream repositories:

- **[soliplex/soliplex](https://github.com/soliplex/soliplex)** - Core Platform
- **[soliplex/ingester](https://github.com/soliplex/ingester)** - Document Ingestion
- **[soliplex/ingester-agents](https://github.com/soliplex/ingester-agents)** - Ingester Agents
- **[soliplex/chatbot](https://github.com/soliplex/chatbot)** - Chatbot Interface
- **[soliplex/flutter](https://github.com/soliplex/flutter)** - Flutter Frontend
- **[soliplex/ag-ui](https://github.com/soliplex/ag-ui)** - AG UI Components

## Documentation Synchronization

Documentation is automatically synchronized using GitHub Actions:

### Automatic Sync

- **Daily**: Syncs all repositories at 2 AM UTC
- **On Demand**: Triggered when upstream repositories publish changes via `repository_dispatch`
- **Manual**: Can be triggered manually via GitHub Actions UI

### How It Works

1. The [sync-docs.yml](.github/workflows/sync-docs.yml) workflow runs on schedule or trigger
2. For each repository, [sync-repo-docs.sh](scripts/sync-repo-docs.sh) fetches documentation using git sparse checkout
3. Documentation is copied to corresponding `docs/` subdirectories
4. Changes are committed and pushed automatically
5. GitHub Pages builds and deploys the updated site

### Manual Sync

To manually sync documentation from specific repositories:

1. Go to [Actions → Sync Documentation from Repos](https://github.com/soliplex/soliplex.github.io/actions/workflows/sync-docs.yml)
2. Click "Run workflow"
3. Select which repository to sync (or "all")
4. Click "Run workflow"

### Local Testing

To test documentation sync locally:

```bash
# Sync specific repository
./scripts/sync-repo-docs.sh soliplex/soliplex docs/soliplex docs

# Sync all repositories
./scripts/sync-repo-docs.sh soliplex/soliplex docs/soliplex docs
./scripts/sync-repo-docs.sh soliplex/ingester docs/ingester docs
```

**Note**: Synced directories (docs/soliplex/, docs/ingester/, etc.) are in .gitignore and should not be committed.

## Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Or install directly
pip install mkdocs-material

# Serve locally (default port 8001)
mkdocs serve

# Serve on different port
mkdocs serve -a localhost:8002
```

The documentation site will be available at http://127.0.0.1:8001/

### Building

```bash
# Build static site
mkdocs build

# Output will be in site/
```

### Project Structure

```
soliplex.github.io/
├── .github/
│   └── workflows/
│       ├── build-docs.yml    # Build and deploy to GitHub Pages
│       └── sync-docs.yml      # Sync from upstream repos
├── scripts/
│   └── sync-repo-docs.sh      # Sync script
├── docs/
│   ├── index.md               # Landing page (manually maintained)
│   ├── soliplex/              # Auto-synced from soliplex/soliplex
│   ├── ingester/              # Auto-synced from soliplex/ingester
│   ├── agents/                # Auto-synced from soliplex/ingester-agents
│   ├── chatbot/               # Auto-synced from soliplex/chatbot
│   ├── flutter/               # Auto-synced from soliplex/flutter
│   └── ag-ui/                 # Auto-synced from soliplex/ag-ui
├── mkdocs.yml                 # MkDocs configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

### Adding New Repositories

To add documentation from a new repository:

1. Edit [.github/workflows/sync-docs.yml](.github/workflows/sync-docs.yml):
   - Add the repository to the `workflow_dispatch` input options
   - Add a new sync step using the sync script
   - Add the repository to the commit message generation

2. Update [mkdocs.yml](mkdocs.yml):
   - Add navigation entries for the new documentation

3. Update [.gitignore](.gitignore):
   - Add the new docs subdirectory to ignored paths

4. Update this README:
   - Add the repository to the Overview list

## Troubleshooting

### Sync Issues

If documentation sync fails:

1. Check the [Sync Docs workflow runs](https://github.com/soliplex/soliplex.github.io/actions/workflows/sync-docs.yml)
2. Verify the upstream repository has a `docs/` directory or specified path
3. Check that the sync script has correct permissions (`chmod +x scripts/sync-repo-docs.sh`)
4. Try running the sync script locally to identify issues

### Build Issues

If the documentation build fails:

1. Check the [Build Docs workflow runs](https://github.com/soliplex/soliplex.github.io/actions/workflows/build-docs.yml)
2. Verify all navigation paths in `mkdocs.yml` point to existing files
3. Check for Markdown syntax errors in documentation files
4. Test the build locally with `mkdocs build --strict`

### Local Development

If local development server has issues:

```bash
# Clean build cache
rm -rf site/ .cache/

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Serve with verbose output
mkdocs serve --verbose
```

## Contributing

### Documentation Updates

**Do not edit synced directories directly** (docs/soliplex/, docs/ingester/, etc.). These are automatically overwritten.

To update documentation:

1. Make changes in the upstream repository (e.g., soliplex/soliplex)
2. Documentation will sync automatically within 24 hours
3. Or manually trigger sync via GitHub Actions

### Site Configuration

To update site configuration or landing page:

1. Edit `mkdocs.yml` for navigation and theme settings
2. Edit `docs/index.md` for the landing page content
3. Create a pull request with changes

## Related Repositories

- [soliplex/soliplex](https://github.com/soliplex/soliplex) - Core Platform
- [soliplex/ingester](https://github.com/soliplex/ingester) - Document Ingestion System
- [soliplex/ingester-agents](https://github.com/soliplex/ingester-agents) - Ingester Agent Framework
- [soliplex/chatbot](https://github.com/soliplex/chatbot) - Chatbot Interface
- [soliplex/flutter](https://github.com/soliplex/flutter) - Flutter Mobile/Web Frontend
- [soliplex/ag-ui](https://github.com/soliplex/ag-ui) - AG UI Component Library

## License

Documentation is licensed under the same terms as the respective upstream projects.
