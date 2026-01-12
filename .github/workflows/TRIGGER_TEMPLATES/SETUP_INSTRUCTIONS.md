# Setup Instructions for Automated Documentation Triggers

## Option A: Using Organization Secret (Recommended)

**✅ Best for organizations with multiple repositories**

### Advantages
- Single token to manage (set once, use everywhere)
- Automatically available to all repos in the organization
- No need to add secret to each individual repository
- Easier to rotate (update in one place)
- Centralized security management

### Setup Steps

#### 1. Create GitHub Personal Access Token (PAT)

1. Go to https://github.com/settings/tokens (or Settings → Developer settings → Personal access tokens → Tokens (classic))
2. Click "Generate new token" → "Generate new token (classic)"
3. Configure the token:
   - **Name**: `Docs Deploy Token`
   - **Expiration**: 90 days (or "No expiration" if your org policy allows)
   - **Scopes**: Select only `public_repo` (for public repositories) or `repo` (for private repos)
4. Click "Generate token"
5. **Copy the token immediately** (you won't see it again!)

#### 2. Add Token as Organization Secret

1. Go to your organization: https://github.com/orgs/soliplex/settings/secrets/actions
2. Click "New organization secret"
3. Configure:
   - **Name**: `DOCS_DEPLOY_TOKEN`
   - **Value**: Paste the PAT you created
   - **Repository access**: Select "Selected repositories"
   - Choose all 7 submodule repositories:
     - ✅ soliplex/soliplex
     - ✅ soliplex/ingester
     - ✅ soliplex/ingester-agents
     - ✅ soliplex/ag-ui
     - ✅ soliplex/pdf-splitter
     - ✅ soliplex/flutter
     - ✅ soliplex/chatbot
4. Click "Add secret"

**Note**: The organization secret is automatically available to workflows in selected repos as `secrets.DOCS_DEPLOY_TOKEN`

#### 3. Install Workflow in Each Submodule

Copy `submodule-trigger-template.yml` to each submodule:

```bash
# For each submodule repository
cd /path/to/submodule-repo
mkdir -p .github/workflows
cp /path/to/soliplex.github.io/.github/workflows/TRIGGER_TEMPLATES/submodule-trigger-template.yml \
   .github/workflows/trigger-docs-deploy.yml

# Commit and push
git add .github/workflows/trigger-docs-deploy.yml
git commit -m "ci: add documentation rebuild trigger"
git push
```

Repositories that need this workflow:
- [ ] soliplex/soliplex
- [ ] soliplex/ingester
- [ ] soliplex/ingester-agents
- [ ] soliplex/ag-ui
- [ ] soliplex/pdf-splitter
- [ ] soliplex/flutter
- [ ] soliplex/chatbot

#### 4. Update Main Documentation Workflow

Already done! The `build-docs.yml` workflow needs to listen for `repository_dispatch` events.

Add this to `.github/workflows/build-docs.yml` (if not already present):

```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:
  repository_dispatch:  # ← Add this
    types: [docs_update]  # ← Add this
```

#### 5. Test the Setup

1. Make a documentation change in any submodule:
   ```bash
   cd projects/soliplex/docs
   echo "Test update" >> test.md
   git add test.md
   git commit -m "docs: test trigger"
   git push
   ```

2. Check that two workflows run:
   - In the submodule: "Trigger Documentation Rebuild"
   - In soliplex.github.io: "Build and Deploy Docs"

3. Verify the docs site updates: https://soliplex.github.io/

---

## Option B: Using Repository Secrets (Alternative)

**⚠️ Use only if you don't have organization admin access**

### Setup Steps

1. Create the same PAT as above
2. Add the secret to **each individual repository**:
   ```
   Go to each repo → Settings → Secrets and variables → Actions → New repository secret
   Name: DOCS_DEPLOY_TOKEN
   Value: <paste PAT>
   ```
3. Repeat for all 7 repositories
4. Install workflow files (same as Option A step 3)

### Disadvantages
- Must add secret to each repo individually (7 times)
- Must update in 7 places when rotating token
- More maintenance overhead

---

## Token Management

### Security Best Practices

1. **Use minimal permissions**: Only `public_repo` scope needed
2. **Set expiration**: Use 90-day expiration if possible
3. **Rotate regularly**: Set calendar reminder to rotate token
4. **Document token owner**: Keep track of which account created the token
5. **Audit access**: Regularly review which repos have access

### Token Rotation Process

When the token expires or needs rotation:

**With Organization Secret (Easy)**:
1. Create new PAT (same steps as above)
2. Go to org secrets: https://github.com/orgs/soliplex/settings/secrets/actions
3. Click `DOCS_DEPLOY_TOKEN` → Update
4. Paste new token value
5. Done! All repos automatically use new token

**With Repository Secrets (Tedious)**:
1. Create new PAT
2. Update secret in all 7 repositories individually
3. Test each one

### Troubleshooting Token Issues

**Error: "Bad credentials"**
- Token has expired or been revoked
- Token doesn't have correct permissions
- Solution: Create new token with `public_repo` scope

**Error: "Resource not accessible by integration"**
- Token doesn't have access to target repository
- Solution: Ensure token has `public_repo` or `repo` scope

**Error: 404 Not Found**
- Repository path is incorrect
- Target repository doesn't exist
- Solution: Verify repository names

---

## Verification Checklist

After setup, verify:

- [ ] Organization secret `DOCS_DEPLOY_TOKEN` exists
- [ ] Secret has access to all 7 submodule repositories
- [ ] Token has `public_repo` scope
- [ ] Workflow file exists in all 7 submodules
- [ ] Main docs workflow listens for `repository_dispatch`
- [ ] Test trigger works from at least one submodule
- [ ] Docs site rebuilds automatically
- [ ] Set calendar reminder for token rotation

---

## Cost and Performance

**GitHub Actions minutes used per documentation update**:
- Submodule trigger workflow: ~30 seconds (0.5 minutes)
- Main docs build workflow: ~3-5 minutes
- **Total: ~3.5-5.5 minutes per docs update**

**With free tier (2,000 minutes/month)**:
- Can handle **~360-570 documentation updates/month**
- That's **12-19 updates per day**
- More than sufficient for typical documentation changes

---

## Alternative: Using GitHub App (Future Enhancement)

For organizations with many repositories (>20), consider creating a GitHub App:

**Advantages**:
- No token expiration
- Better security model
- Automatic token refresh
- Fine-grained permissions

**Disadvantages**:
- More complex setup
- Requires webhook receiver
- Overkill for 7 repositories

**Recommendation**: Stick with organization secret for now, migrate to GitHub App if scaling beyond 20 repositories.

---

## Quick Setup Script

```bash
#!/bin/bash
# Quick setup script for adding workflow to all submodules

TEMPLATE="submodule-trigger-template.yml"
REPOS=(
  "soliplex"
  "ingester"
  "ingester-agents"
  "ag-ui"
  "pdf-splitter"
  "flutter"
  "chatbot"
)

for repo in "${REPOS[@]}"; do
  echo "Setting up $repo..."
  cd "projects/$repo" || continue

  mkdir -p .github/workflows
  cp "../../.github/workflows/TRIGGER_TEMPLATES/$TEMPLATE" \
     .github/workflows/trigger-docs-deploy.yml

  git add .github/workflows/trigger-docs-deploy.yml
  git commit -m "ci: add documentation rebuild trigger"

  echo "✓ Committed to $repo"
  cd ../..
done

echo "
✅ Setup complete!

Next steps:
1. Review commits in each submodule
2. Push to remote: cd projects/<repo> && git push
3. Test with a documentation change
"
```

---

**Last Updated**: 2026-01-09
