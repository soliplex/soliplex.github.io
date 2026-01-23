#!/bin/bash
set -e

echo "========================================="
echo "Setting up documentation triggers"
echo "for all 7 submodule repositories"
echo "========================================="
echo ""

REPOS=("soliplex" "ingester" "ingester-agents" "ag-ui" "pdf-splitter" "flutter" "chatbot")
SUCCESS=0
FAILED=0

for repo in "${REPOS[@]}"; do
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Processing: $repo"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  cd "projects/$repo" || { echo "❌ Failed to cd into $repo"; ((FAILED++)); continue; }

  # Update main branch
  echo "📥 Updating main branch..."
  git checkout main 2>/dev/null || git checkout master 2>/dev/null
  git pull origin $(git branch --show-current)

  # Check if branch already exists
  if git rev-parse --verify docs/add-rebuild-trigger >/dev/null 2>&1; then
    echo "⚠️  Branch docs/add-rebuild-trigger already exists"
    read -p "Delete and recreate? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      git branch -D docs/add-rebuild-trigger
    else
      echo "Skipping $repo"
      cd ../..
      continue
    fi
  fi

  # Create feature branch
  echo "🌿 Creating branch: docs/add-rebuild-trigger"
  git checkout -b docs/add-rebuild-trigger

  # Create directory and copy template
  echo "📁 Creating .github/workflows directory"
  mkdir -p .github/workflows

  echo "📄 Copying workflow template"
  cp ../../.github/workflows/TRIGGER_TEMPLATES/submodule-trigger-template.yml .github/workflows/trigger-docs-deploy.yml

  # Commit and push
  echo "💾 Committing changes"
  git add .github/workflows/trigger-docs-deploy.yml
  git commit -m "ci: add documentation rebuild trigger

This workflow automatically triggers a documentation rebuild on
soliplex.github.io when markdown documentation changes are pushed.

Changes:
- Add .github/workflows/trigger-docs-deploy.yml
- Triggers on docs/**/*.md, docs/**/*.mdx, and README.md changes
- Uses organization secret DOCS_DEPLOY_TOKEN
- Sends repository_dispatch event to soliplex.github.io"

  echo "📤 Pushing to remote"
  git push -u origin docs/add-rebuild-trigger

  echo "✅ $repo setup complete"
  ((SUCCESS++))

  # Return to main
  git checkout main 2>/dev/null || git checkout master 2>/dev/null
  cd ../..
  echo ""
done

echo "========================================="
echo "Summary"
echo "========================================="
echo "✅ Success: $SUCCESS"
echo "❌ Failed: $FAILED"
echo ""

if [ $SUCCESS -gt 0 ]; then
  echo "Next steps:"
  echo "1. Create pull requests (see below)"
  echo "2. Review and merge PRs"
  echo "3. Test with a docs change"
  echo ""
  echo "To create PRs with gh CLI:"
  echo "  bash create-prs.sh"
fi
