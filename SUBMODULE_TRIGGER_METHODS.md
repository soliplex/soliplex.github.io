# Methods to Trigger Documentation Builds from Submodule Updates

This document explores various methods to automatically trigger the documentation build workflow in `soliplex.github.io` when any of the 7 submodule projects are updated.

## Overview

**Challenge**: The documentation site (`soliplex.github.io`) aggregates docs from 7 submodule repositories. When documentation changes in any submodule, we want to automatically rebuild and deploy the main documentation site.

**Submodules**:
- soliplex/soliplex
- soliplex/ingester
- soliplex/ingester-agents
- soliplex/ag-ui
- soliplex/pdf-splitter
- soliplex/flutter
- soliplex/chatbot

## Method 1: Repository Dispatch (Recommended)

### How It Works

1. Each submodule has a workflow that triggers on push
2. The workflow sends a `repository_dispatch` event to `soliplex.github.io`
3. The docs workflow listens for these events and rebuilds

### Pros
- ✅ Real-time updates when any submodule changes
- ✅ Works across repositories
- ✅ Simple to implement
- ✅ Explicit control over when to trigger
- ✅ Can include metadata about what changed

### Cons
- ⚠️ Requires Personal Access Token (PAT) or GitHub App
- ⚠️ Need to add workflow to each submodule
- ⚠️ Token needs `repo` or `public_repo` scope

### Implementation

#### Step 1: Create a GitHub Token

Create a Personal Access Token with `repo` or `public_repo` scope:
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `public_repo` scope (for public repos)
3. Save token securely

#### Step 2: Add Token as Secret

Add the token to each submodule repository:
1. Go to each submodule repo → Settings → Secrets and variables → Actions
2. Create secret: `DOCS_DEPLOY_TOKEN` = your PAT

#### Step 3: Add Workflow to Each Submodule

Create `.github/workflows/trigger-docs-deploy.yml` in each submodule:

```yaml
name: Trigger Docs Deployment

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - 'README.md'
      - '.github/workflows/trigger-docs-deploy.yml'

jobs:
  trigger-docs:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger documentation rebuild
        run: |
          curl -X POST \
            -H "Accept: application/vnd.github.v3+json" \
            -H "Authorization: token ${{ secrets.DOCS_DEPLOY_TOKEN }}" \
            https://api.github.com/repos/soliplex/soliplex.github.io/dispatches \
            -d '{"event_type":"docs_update","client_payload":{"repository":"${{ github.repository }}","ref":"${{ github.ref }}"}}'
```

#### Step 4: Update Main Docs Workflow

Update `.github/workflows/build-docs.yml` in `soliplex.github.io`:

```yaml
name: Build and Deploy Docs

on:
  push:
    branches: [main]
  workflow_dispatch:
  repository_dispatch:  # Add this
    types: [docs_update]

# ... rest of workflow
```

### Cost Analysis
- Token management overhead: Low
- Maintenance: Medium (need to add workflow to each submodule)
- Reliability: High

---

## Method 2: Scheduled Polling (Simplest)

### How It Works

Use GitHub Actions scheduled workflows to check for updates periodically.

### Pros
- ✅ No tokens needed
- ✅ No changes to submodules
- ✅ Simple to implement
- ✅ Works reliably

### Cons
- ⚠️ Delayed updates (5-60 minute intervals)
- ⚠️ Unnecessary builds if nothing changed
- ⚠️ Consumes Actions minutes even without changes

### Implementation

Update `.github/workflows/build-docs.yml`:

```yaml
name: Build and Deploy Docs

on:
  push:
    branches: [main]
  workflow_dispatch:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          submodules: recursive
          fetch-depth: 0

      - name: Check for submodule updates
        id: check_updates
        run: |
          git submodule update --remote
          if git diff --quiet HEAD; then
            echo "changed=false" >> $GITHUB_OUTPUT
          else
            echo "changed=true" >> $GITHUB_OUTPUT
          fi

      - name: Update submodules
        if: steps.check_updates.outputs.changed == 'true'
        run: |
          git config user.name github-actions[bot]
          git config user.email 41898282+github-actions[bot]@users.noreply.github.com
          git add .
          git commit -m "docs: update submodules"
          git push

      # ... rest of build steps only if changed
```

### Cost Analysis
- Token management: None
- Maintenance: Very low
- Reliability: High
- Actions minutes: Higher consumption

---

## Method 3: GitHub App + Webhooks (Enterprise)

### How It Works

Create a GitHub App that listens to webhooks from all repositories and triggers workflows.

### Pros
- ✅ Real-time updates
- ✅ No token rotation needed
- ✅ Fine-grained permissions
- ✅ Scalable to many repositories

### Cons
- ⚠️ Complex setup
- ⚠️ Requires hosting webhook receiver
- ⚠️ Overkill for 7 repositories
- ⚠️ More moving parts to maintain

### Implementation Overview

1. Create GitHub App with `contents:read` and `actions:write` permissions
2. Deploy webhook receiver (AWS Lambda, Cloud Function, etc.)
3. Configure webhooks on each submodule
4. Receiver triggers workflow via GitHub API

**Not recommended** for this use case due to complexity.

---

## Method 4: Hybrid - Webhook with GitHub Actions

### How It Works

Use a workflow in each submodule that calls the GitHub API to trigger the docs workflow.

### Pros
- ✅ Real-time updates
- ✅ No external infrastructure
- ✅ Moderate complexity
- ✅ Standard GitHub Actions patterns

### Cons
- ⚠️ Requires token in each repo
- ⚠️ Similar to Method 1 but more flexible

### Implementation

Same as Method 1 but uses `workflow_dispatch` instead of `repository_dispatch`:

```yaml
# In each submodule
name: Trigger Docs Deployment

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - 'README.md'

jobs:
  trigger-docs:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger documentation workflow
        run: |
          curl -X POST \
            -H "Accept: application/vnd.github.v3+json" \
            -H "Authorization: token ${{ secrets.DOCS_DEPLOY_TOKEN }}" \
            https://api.github.com/repos/soliplex/soliplex.github.io/actions/workflows/build-docs.yml/dispatches \
            -d '{"ref":"main","inputs":{}}'
```

---

## Method 5: Dependabot for Submodule Updates

### How It Works

Use Dependabot to automatically create PRs when submodules have updates.

### Pros
- ✅ Visual review before deployment
- ✅ No tokens needed in submodules
- ✅ Audit trail via PRs
- ✅ Can batch multiple updates

### Cons
- ⚠️ Requires manual PR merge (can be automated)
- ⚠️ Delayed updates
- ⚠️ More GitHub notifications

### Implementation

Create `.github/dependabot.yml` in `soliplex.github.io`:

```yaml
version: 2
updates:
  - package-ecosystem: "gitsubmodule"
    directory: "/"
    schedule:
      interval: "daily"
      time: "09:00"
    open-pull-requests-limit: 10
    labels:
      - "documentation"
      - "dependencies"
    commit-message:
      prefix: "docs"
      include: "scope"
```

Then enable auto-merge for Dependabot PRs:

```yaml
# .github/workflows/auto-merge-dependabot.yml
name: Auto-merge Dependabot

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  auto-merge:
    runs-on: ubuntu-latest
    if: github.actor == 'dependabot[bot]'
    steps:
      - name: Enable auto-merge
        run: gh pr merge --auto --squash "$PR_URL"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Comparison Matrix

| Method | Real-time | Complexity | Token Needed | Maintenance | Recommended For |
|--------|-----------|------------|--------------|-------------|-----------------|
| **Repository Dispatch** | ✅ Yes | Medium | ✅ Yes | Medium | Production use |
| **Scheduled Polling** | ❌ No (15-60min) | Low | ❌ No | Low | Quick setup, low traffic |
| **GitHub App** | ✅ Yes | High | ❌ No | High | Large scale (>20 repos) |
| **Workflow Dispatch** | ✅ Yes | Medium | ✅ Yes | Medium | Similar to Method 1 |
| **Dependabot** | ❌ No (daily) | Low | ❌ No | Low | Review before deploy |

---

## Recommended Approach

### Option A: For Immediate Production (Recommended)

**Use Method 1 (Repository Dispatch) + Method 5 (Dependabot backup)**

**Rationale**:
- Real-time updates via repository_dispatch
- Dependabot provides safety net and audit trail
- Best balance of automation and control

**Setup Steps**:
1. Implement Method 1 for real-time triggers
2. Implement Method 5 for safety and auditing
3. Auto-merge Dependabot PRs for seamless updates

### Option B: For Quick Start (Easiest)

**Use Method 2 (Scheduled Polling)**

**Rationale**:
- Zero configuration in submodules
- No token management
- Good enough for most documentation updates

**Setup Steps**:
1. Add scheduled trigger to main workflow
2. Check for changes before building
3. Commit submodule updates automatically

### Option C: Best of Both Worlds

**Combine Methods 1 + 2**

**Rationale**:
- Real-time when possible (repository_dispatch)
- Fallback polling catches any missed updates
- Most reliable option

---

## Implementation Checklist

### For Method 1 (Repository Dispatch)

- [ ] Create GitHub Personal Access Token
- [ ] Add `DOCS_DEPLOY_TOKEN` secret to all 7 submodules
- [ ] Create `.github/workflows/trigger-docs-deploy.yml` in each submodule
- [ ] Update `build-docs.yml` to listen for `repository_dispatch`
- [ ] Test with a docs change in one submodule
- [ ] Verify documentation rebuilds automatically
- [ ] Document the process for new submodules

### For Method 2 (Scheduled Polling)

- [ ] Add `schedule` trigger to `build-docs.yml`
- [ ] Add change detection logic
- [ ] Add conditional build steps
- [ ] Test scheduled execution
- [ ] Monitor Actions usage

### For Method 5 (Dependabot)

- [ ] Create `.github/dependabot.yml`
- [ ] Enable Dependabot
- [ ] Create auto-merge workflow
- [ ] Test with manual submodule update
- [ ] Configure notification preferences

---

## Testing Strategy

1. **Test single submodule update**:
   ```bash
   cd projects/soliplex
   echo "test" >> docs/test.md
   git add . && git commit -m "test: docs trigger"
   git push
   # Verify docs site rebuilds
   ```

2. **Test multiple simultaneous updates**: Update 2-3 submodules within 1 minute

3. **Test edge cases**:
   - Update to non-docs files (shouldn't trigger)
   - Update to README.md (should trigger)
   - Empty commit (shouldn't trigger)

4. **Monitor costs**: Check GitHub Actions usage after 1 week

---

## Security Considerations

### Token Security
- Use tokens with minimal required permissions
- Rotate tokens quarterly
- Use GitHub App tokens if scaling beyond 7 repos
- Never commit tokens to repository

### Access Control
- Limit who can trigger documentation builds
- Use branch protection on main branch
- Require PR reviews for submodule commits
- Enable audit logging

---

## Rollback Plan

If automated triggers cause issues:

1. **Disable triggers**: Remove `repository_dispatch` from workflow
2. **Manual fallback**: Use `workflow_dispatch` for manual triggers
3. **Revert workflow**: Restore previous workflow version
4. **Investigation**: Review workflow logs and API calls

---

## Cost Estimation

**GitHub Actions Minutes (Free tier: 2000 min/month)**

### Method 1 (Repository Dispatch)
- Per trigger: ~3-5 minutes
- Estimated triggers: 20-50/month (assuming 1-2 docs updates per submodule per week)
- **Total: 60-250 minutes/month**

### Method 2 (Scheduled Every 15 min)
- Per run: ~2 minutes (if no changes) or ~5 minutes (with changes)
- Runs per month: 2,880
- **Total: 5,760 minutes/month (exceeds free tier!)**

### Method 2 (Scheduled Every Hour)
- Runs per month: 720
- **Total: 1,440 minutes/month (within free tier)**

**Recommendation**: Use Method 1 for cost efficiency

---

## Future Enhancements

1. **Selective builds**: Only rebuild affected sections
2. **Build caching**: Cache unchanged project docs
3. **Parallel builds**: Build multiple projects simultaneously
4. **Preview deployments**: Deploy to staging before production
5. **Notifications**: Slack/email on successful deployment

---

**Last Updated**: 2026-01-09
