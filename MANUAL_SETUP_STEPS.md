# Manual Setup Steps for Documentation Triggers

Since the automated script requires gh CLI setup, here are manual steps to configure each submodule.

## Prerequisites

✅ Organization secret `DOCS_DEPLOY_TOKEN` created
✅ Secret has access to all 7 submodule repositories
✅ Path filters updated to only trigger on markdown files

## Setup for Each Submodule

Run these commands for each of the 7 repositories. Replace `<REPO>` with the repository name.

### Repositories to Configure

1. soliplex
2. ingester
3. ingester-agents
4. ag-ui
5. pdf-splitter
6. flutter
7. chatbot

---

## Step-by-Step Commands

### For each repository, run:

```bash
# Navigate to the submodule
cd projects/<REPO>

# Ensure you're on the main branch and up to date
git checkout main
git pull origin main

# Create feature branch
git checkout -b docs/add-rebuild-trigger

# Create workflows directory if it doesn't exist
mkdir -p .github/workflows

# Copy the template
cp ../../.github/workflows/TRIGGER_TEMPLATES/submodule-trigger-template.yml .github/workflows/trigger-docs-deploy.yml

# Add and commit
git add .github/workflows/trigger-docs-deploy.yml
git commit -m "ci: add documentation rebuild trigger

This workflow automatically triggers a documentation rebuild on
soliplex.github.io when markdown documentation changes are pushed.

Changes:
- Add .github/workflows/trigger-docs-deploy.yml
- Triggers on docs/**/*.md, docs/**/*.mdx, and README.md changes
- Uses organization secret DOCS_DEPLOY_TOKEN
- Sends repository_dispatch event to soliplex.github.io"

# Push to remote
git push -u origin docs/add-rebuild-trigger

# Return to parent directory
cd ../..
```

### Create Pull Requests

After pushing all branches, create PRs manually via GitHub web interface or use gh CLI:

```bash
# If gh CLI is configured and authenticated:
cd projects/<REPO>
gh pr create \
  --title "ci: Add documentation rebuild trigger" \
  --body "See commit message for details" \
  --label "ci" \
  --label "documentation"
cd ../..
```

Or visit each repository on GitHub and create PR from the branch.

---

## Quick Commands for All Repos

Copy and paste this entire block to set up all 7 repositories at once:

```bash
#!/bin/bash
# Navigate to the soliplex.github.io directory first

REPOS=("soliplex" "ingester" "ingester-agents" "ag-ui" "pdf-splitter" "flutter" "chatbot")

for repo in "${REPOS[@]}"; do
  echo "========================================="
  echo "Setting up: $repo"
  echo "========================================="

  cd "projects/$repo" || { echo "Failed to cd into $repo"; continue; }

  # Update main branch
  git checkout main
  git pull origin main

  # Create feature branch
  git checkout -b docs/add-rebuild-trigger

  # Create directory and copy template
  mkdir -p .github/workflows
  cp ../../.github/workflows/TRIGGER_TEMPLATES/submodule-trigger-template.yml .github/workflows/trigger-docs-deploy.yml

  # Commit and push
  git add .github/workflows/trigger-docs-deploy.yml
  git commit -m "ci: add documentation rebuild trigger

This workflow automatically triggers a documentation rebuild on
soliplex.github.io when markdown documentation changes are pushed.

Changes:
- Add .github/workflows/trigger-docs-deploy.yml
- Triggers on docs/**/*.md, docs/**/*.mdx, and README.md changes
- Uses organization secret DOCS_DEPLOY_TOKEN
- Sends repository_dispatch event to soliplex.github.io"

  git push -u origin docs/add-rebuild-trigger

  echo "✓ $repo setup complete"
  cd ../..
  echo ""
done

echo "========================================="
echo "All repositories configured!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Create pull requests for each repository"
echo "2. Review and merge the PRs"
echo "3. Test by updating documentation in any repo"
```

---

## Verification Checklist

After setup, verify each repository:

- [ ] **soliplex**: Branch created and pushed
- [ ] **ingester**: Branch created and pushed
- [ ] **ingester-agents**: Branch created and pushed
- [ ] **ag-ui**: Branch created and pushed
- [ ] **pdf-splitter**: Branch created and pushed
- [ ] **flutter**: Branch created and pushed
- [ ] **chatbot**: Branch created and pushed

---

## Create PRs (Using gh CLI)

If gh CLI is set up, run this to create all PRs:

```bash
#!/bin/bash
REPOS=("soliplex" "ingester" "ingester-agents" "ag-ui" "pdf-splitter" "flutter" "chatbot")

for repo in "${REPOS[@]}"; do
  echo "Creating PR for $repo..."
  cd "projects/$repo"

  gh pr create \
    --title "ci: Add documentation rebuild trigger" \
    --body "## Summary

This PR adds an automated workflow to trigger documentation rebuilds on [soliplex.github.io](https://github.com/soliplex/soliplex.github.io) whenever markdown documentation changes are pushed to this repository.

## Changes

- Adds \`.github/workflows/trigger-docs-deploy.yml\`
- Triggers on changes to:
  - \`docs/**/*.md\` files
  - \`docs/**/*.mdx\` files
  - \`README.md\` file
  - The workflow file itself

## How It Works

1. When markdown documentation changes are pushed to \`main\`/\`master\` branch
2. This workflow sends a \`repository_dispatch\` event to \`soliplex.github.io\`
3. The main documentation site rebuilds automatically with the latest changes
4. Updated documentation is deployed to https://soliplex.github.io/

## Prerequisites

✅ Organization secret \`DOCS_DEPLOY_TOKEN\` is configured with access to this repository.

## Testing

After merging:
1. Make a change to any markdown file in \`docs/\` or \`README.md\`
2. Push to main branch
3. Check [soliplex.github.io Actions](https://github.com/soliplex/soliplex.github.io/actions) to see the documentation rebuild
4. Verify the changes appear on the live site

---

Part of the multi-project documentation automation initiative." \
    --label "ci" \
    --label "documentation"

  cd ../..
done
```

---

## Create PRs (Manually via GitHub)

If gh CLI isn't available, create PRs manually:

1. Go to each repository on GitHub
2. You should see a yellow banner about the recently pushed branch
3. Click "Compare & pull request"
4. Fill in:
   - **Title**: `ci: Add documentation rebuild trigger`
   - **Labels**: `ci`, `documentation`
   - **Description**: Use the template from the gh CLI command above
5. Create the PR

Repository URLs:
- https://github.com/soliplex/soliplex/compare/docs/add-rebuild-trigger?expand=1
- https://github.com/soliplex/ingester/compare/docs/add-rebuild-trigger?expand=1
- https://github.com/soliplex/ingester-agents/compare/docs/add-rebuild-trigger?expand=1
- https://github.com/soliplex/ag-ui/compare/docs/add-rebuild-trigger?expand=1
- https://github.com/soliplex/pdf-splitter/compare/docs/add-rebuild-trigger?expand=1
- https://github.com/soliplex/flutter/compare/docs/add-rebuild-trigger?expand=1
- https://github.com/soliplex/chatbot/compare/docs/add-rebuild-trigger?expand=1

---

## Testing After Merge

Once all PRs are merged, test the automation:

```bash
# Test with the soliplex repository
cd projects/soliplex
git checkout main
git pull origin main

# Make a test change
echo "Test update $(date)" >> docs/test.md
git add docs/test.md
git commit -m "docs: test automated rebuild trigger"
git push origin main

# Wait 1-2 minutes, then check:
# https://github.com/soliplex/soliplex.github.io/actions

# You should see a new workflow run triggered by repository_dispatch
```

---

## Troubleshooting

### Workflow doesn't trigger

1. Check organization secret exists and has access to the repository
2. Verify the workflow file is on the main/master branch (not just in PR)
3. Check that the path filter matches your change (must be .md or .mdx in docs/)
4. View Actions tab in the submodule repo to see if trigger workflow ran

### Build fails on soliplex.github.io

1. Check the workflow logs: https://github.com/soliplex/soliplex.github.io/actions
2. Verify submodules updated correctly
3. Check build-docs.py output for errors
4. Ensure mkdocs.yml navigation references are valid

---

**Last Updated**: 2026-01-09
