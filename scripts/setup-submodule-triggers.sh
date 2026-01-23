#!/bin/bash
# Setup script to add documentation trigger workflow to all submodule repositories
# Creates feature branches and pull requests due to branch protection
#
# Prerequisites:
#   - gh CLI installed (https://cli.github.com/)
#   - gh auth login (authenticated)
#   - Organization secret DOCS_DEPLOY_TOKEN configured
#
# Usage:
#   ./scripts/setup-submodule-triggers.sh [--dry-run]
#
# Options:
#   --dry-run    Show what would be done without making changes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATE_FILE="$ROOT_DIR/.github/workflows/TRIGGER_TEMPLATES/submodule-trigger-template.yml"
TARGET_FILE=".github/workflows/trigger-docs-deploy.yml"
BRANCH_NAME="docs/add-rebuild-trigger"

REPOS=(
  "soliplex"
  "ingester"
  "ingester-agents"
  "ag-ui"
  "pdf-splitter"
  "flutter"
  "chatbot"
)

DRY_RUN=false

# Parse arguments
for arg in "$@"; do
  case $arg in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--dry-run]"
      echo ""
      echo "Setup documentation trigger workflows in all submodule repositories"
      echo "Creates feature branches and pull requests"
      echo ""
      echo "Prerequisites:"
      echo "  - gh CLI installed and authenticated"
      echo "  - Organization secret DOCS_DEPLOY_TOKEN configured"
      echo ""
      echo "Options:"
      echo "  --dry-run    Show what would be done without making changes"
      echo "  -h, --help   Show this help message"
      exit 0
      ;;
  esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Submodule Trigger Workflow Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}🔍 DRY RUN MODE - No changes will be made${NC}"
  echo ""
fi

# Check for gh CLI
if ! command -v gh &> /dev/null; then
  echo -e "${RED}❌ gh CLI not found${NC}"
  echo -e "${YELLOW}   Install from: https://cli.github.com/${NC}"
  exit 1
fi

# Check gh auth status
if ! gh auth status &> /dev/null; then
  echo -e "${RED}❌ Not authenticated with GitHub${NC}"
  echo -e "${YELLOW}   Run: gh auth login${NC}"
  exit 1
fi

# Check template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo -e "${RED}❌ Template file not found: $TEMPLATE_FILE${NC}"
  exit 1
fi

echo -e "📝 Template: $(basename "$TEMPLATE_FILE")"
echo -e "📂 Repositories: ${#REPOS[@]}"
echo -e "🌿 Branch name: $BRANCH_NAME"
echo ""

# Track results
SUCCESS_COUNT=0
SKIP_COUNT=0
ERROR_COUNT=0
declare -a PR_URLS

for repo in "${REPOS[@]}"; do
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}Processing: soliplex/$repo${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

  PROJECT_DIR="$ROOT_DIR/projects/$repo"

  if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}⚠️  Directory not found: $PROJECT_DIR${NC}"
    echo -e "${YELLOW}   Skipping...${NC}"
    ((SKIP_COUNT++))
    echo ""
    continue
  fi

  cd "$PROJECT_DIR"

  # Check if already has the workflow on main branch
  git checkout main 2>/dev/null || git checkout master 2>/dev/null || {
    echo -e "${RED}❌ Could not checkout main/master branch${NC}"
    ((ERROR_COUNT++))
    cd "$ROOT_DIR"
    echo ""
    continue
  }

  git pull origin "$(git branch --show-current)" || {
    echo -e "${YELLOW}⚠️  Could not pull latest changes${NC}"
  }

  if [ -f "$TARGET_FILE" ]; then
    echo -e "${YELLOW}⚠️  Workflow already exists: $TARGET_FILE${NC}"

    # Check if it's identical
    if diff -q "$TEMPLATE_FILE" "$TARGET_FILE" > /dev/null 2>&1; then
      echo -e "${GREEN}   ✓ File is identical to template, skipping${NC}"
      ((SKIP_COUNT++))
      cd "$ROOT_DIR"
      echo ""
      continue
    else
      echo -e "${YELLOW}   File differs from template, will update${NC}"
    fi
  fi

  # Check if branch already exists
  if git rev-parse --verify "$BRANCH_NAME" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Branch $BRANCH_NAME already exists${NC}"

    if [ "$DRY_RUN" = true ]; then
      echo -e "${YELLOW}[DRY RUN] Would delete existing branch and recreate${NC}"
    else
      read -p "   Delete and recreate branch? (y/N) " -n 1 -r
      echo
      if [[ $REPLY =~ ^[Yy]$ ]]; then
        git branch -D "$BRANCH_NAME" || {
          echo -e "${RED}❌ Failed to delete branch${NC}"
          ((ERROR_COUNT++))
          cd "$ROOT_DIR"
          echo ""
          continue
        }
      else
        echo -e "${YELLOW}   Skipping...${NC}"
        ((SKIP_COUNT++))
        cd "$ROOT_DIR"
        echo ""
        continue
      fi
    fi
  fi

  if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[DRY RUN] Would create branch: $BRANCH_NAME${NC}"
    echo -e "${YELLOW}[DRY RUN] Would create directory: $(dirname "$TARGET_FILE")${NC}"
    echo -e "${YELLOW}[DRY RUN] Would copy template to: $TARGET_FILE${NC}"
    echo -e "${YELLOW}[DRY RUN] Would commit changes${NC}"
    echo -e "${YELLOW}[DRY RUN] Would push to remote${NC}"
    echo -e "${YELLOW}[DRY RUN] Would create pull request${NC}"
    ((SUCCESS_COUNT++))
  else
    echo "🌿 Creating branch: $BRANCH_NAME"
    git checkout -b "$BRANCH_NAME" || {
      echo -e "${RED}❌ Failed to create branch${NC}"
      ((ERROR_COUNT++))
      cd "$ROOT_DIR"
      echo ""
      continue
    }

    echo "📁 Creating directory: $(dirname "$TARGET_FILE")"
    mkdir -p "$(dirname "$TARGET_FILE")"

    echo "📄 Copying template..."
    cp "$TEMPLATE_FILE" "$TARGET_FILE"

    echo "🔧 Adding file to git..."
    git add "$TARGET_FILE"

    echo "💾 Committing..."
    git commit -m "ci: add documentation rebuild trigger

This workflow automatically triggers a documentation rebuild on
soliplex.github.io when documentation changes are pushed to this repository.

Changes:
- Add .github/workflows/trigger-docs-deploy.yml
- Triggers on docs/** and README.md changes
- Uses organization secret DOCS_DEPLOY_TOKEN
- Sends repository_dispatch event to soliplex.github.io" || {
      echo -e "${RED}❌ Failed to commit${NC}"
      ((ERROR_COUNT++))
      git checkout main 2>/dev/null || git checkout master 2>/dev/null
      git branch -D "$BRANCH_NAME" 2>/dev/null
      cd "$ROOT_DIR"
      echo ""
      continue
    }

    echo "📤 Pushing to remote..."
    git push -u origin "$BRANCH_NAME" || {
      echo -e "${RED}❌ Failed to push to remote${NC}"
      ((ERROR_COUNT++))
      git checkout main 2>/dev/null || git checkout master 2>/dev/null
      git branch -D "$BRANCH_NAME" 2>/dev/null
      cd "$ROOT_DIR"
      echo ""
      continue
    }

    echo "🔀 Creating pull request..."
    PR_URL=$(gh pr create \
      --title "ci: Add documentation rebuild trigger" \
      --body "## Summary

This PR adds an automated workflow to trigger documentation rebuilds on [soliplex.github.io](https://github.com/soliplex/soliplex.github.io) whenever documentation changes are pushed to this repository.

## Changes

- Adds \`.github/workflows/trigger-docs-deploy.yml\`
- Triggers on changes to:
  - \`docs/**\` directory
  - \`README.md\` file
  - The workflow file itself

## How It Works

1. When documentation changes are pushed to \`main\`/\`master\` branch
2. This workflow sends a \`repository_dispatch\` event to \`soliplex.github.io\`
3. The main documentation site rebuilds automatically with the latest changes
4. Updated documentation is deployed to https://soliplex.github.io/

## Prerequisites

✅ Organization secret \`DOCS_DEPLOY_TOKEN\` is already configured with access to this repository.

## Testing

After merging:
1. Make a change to any file in \`docs/\` or \`README.md\`
2. Push to main branch
3. Check [soliplex.github.io Actions](https://github.com/soliplex/soliplex.github.io/actions) to see the documentation rebuild
4. Verify the changes appear on the live site

---

Part of the multi-project documentation automation initiative." \
      --label "ci" \
      --label "documentation") || {
      echo -e "${RED}❌ Failed to create pull request${NC}"
      ((ERROR_COUNT++))
      git checkout main 2>/dev/null || git checkout master 2>/dev/null
      cd "$ROOT_DIR"
      echo ""
      continue
    }

    echo -e "${GREEN}✅ Successfully created PR: $PR_URL${NC}"
    PR_URLS+=("$repo: $PR_URL")
    ((SUCCESS_COUNT++))

    # Return to main branch
    git checkout main 2>/dev/null || git checkout master 2>/dev/null
  fi

  cd "$ROOT_DIR"
  echo ""
done

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Success: $SUCCESS_COUNT${NC}"
echo -e "${YELLOW}⚠️  Skipped: $SKIP_COUNT${NC}"
echo -e "${RED}❌ Errors: $ERROR_COUNT${NC}"
echo ""

if [ ${#PR_URLS[@]} -gt 0 ]; then
  echo -e "${GREEN}📋 Created Pull Requests:${NC}"
  for pr in "${PR_URLS[@]}"; do
    echo -e "   ${BLUE}$pr${NC}"
  done
  echo ""
fi

if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}This was a dry run. To apply changes, run without --dry-run${NC}"
  echo ""
fi

if [ $SUCCESS_COUNT -gt 0 ] && [ "$DRY_RUN" = false ]; then
  echo -e "${GREEN}✨ Next steps:${NC}"
  echo "  1. Review and merge the pull requests"
  echo "  2. Verify organization secret DOCS_DEPLOY_TOKEN has access to all repos"
  echo "  3. After merging, test by making a docs change in any submodule"
  echo "  4. Check https://github.com/soliplex/soliplex.github.io/actions"
  echo ""
  echo "📝 Organization secret check:"
  echo "   https://github.com/orgs/soliplex/settings/secrets/actions"
fi

exit 0
