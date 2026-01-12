# Troubleshooting repository_dispatch Events

## Issue: "Build and Deploy Docs" Not Triggered

If you see only `pages-build-deployment` running but not "Build and Deploy Docs", here are the possible causes and solutions:

### 1. Check if Workflow Actually Ran

`repository_dispatch` events trigger workflows, but they may not appear prominently in the Actions tab.

**To verify:**

1. Go to: https://github.com/soliplex/soliplex.github.io/actions
2. Look for workflow runs with event type "repository_dispatch"
3. Filter by "Event: repository_dispatch" using the dropdown

**What you should see:**
- Workflow name: "Build and Deploy Docs"
- Event: repository_dispatch
- Triggered by: The repository that sent the event (e.g., pdf-splitter)

### 2. Verify the Event Was Sent

Check the submodule repository (e.g., pdf-splitter):

1. Go to: https://github.com/soliplex/pdf-splitter/actions
2. Find the "Trigger Documentation Rebuild" workflow run
3. Check the logs for:
   ```
   ✅ Successfully triggered documentation rebuild
   HTTP 204
   ```

If you see HTTP 204, the event was sent successfully.

### 3. Check Workflow File Location

The workflow must be on the **default branch** (main) to receive `repository_dispatch` events.

**Verify:**
```bash
cd soliplex.github.io
git checkout main
ls -la .github/workflows/build-docs.yml
```

If the file doesn't exist on main, the workflow won't trigger.

**Solution:**
```bash
# Ensure build-docs.yml is committed to main branch
git add .github/workflows/build-docs.yml
git commit -m "ci: add repository_dispatch trigger"
git push origin main
```

### 4. Check Event Type Matches

The submodule workflow sends: `event_type: "docs_update"`

The main workflow listens for: `types: [docs_update]`

**Verify in build-docs.yml:**
```yaml
on:
  repository_dispatch:
    types: [docs_update]  # Must match exactly
```

### 5. Permissions Issue

The workflow needs proper permissions to trigger.

**Verify permissions in build-docs.yml:**
```yaml
permissions:
  contents: write
  pages: write
  id-token: write
```

### 6. Pages-build-deployment vs Build and Deploy Docs

You might be seeing **both** workflows run:

1. **"Build and Deploy Docs"** (our workflow):
   - Triggered by repository_dispatch
   - Updates submodules
   - Runs build-docs.py
   - Runs mkdocs build
   - Pushes to gh-pages branch

2. **"pages-build-deployment"** (GitHub's automatic workflow):
   - Triggered automatically when gh-pages branch updates
   - Deploys the site to GitHub Pages
   - This is NORMAL and expected

**This is correct behavior!** Both should run in sequence:
```
repository_dispatch → Build and Deploy Docs → pushes to gh-pages → pages-build-deployment
```

### 7. Manual Test

Test the repository_dispatch manually:

```bash
# Set your GitHub token
export GITHUB_TOKEN=your_pat_token

# Run test script
cd soliplex.github.io
./test-dispatch.sh

# Watch for the workflow to start
# Check: https://github.com/soliplex/soliplex.github.io/actions
```

### 8. Check Workflow Runs API

Use GitHub API to check for recent workflow runs:

```bash
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/soliplex/soliplex.github.io/actions/runs?event=repository_dispatch \
  | jq '.workflow_runs[] | {name, event, status, conclusion}'
```

### 9. Common Issues and Solutions

#### Issue: Only seeing pages-build-deployment

**Likely cause:** The workflow IS running, but you're filtering incorrectly in the Actions tab.

**Solution:**
- Click "All workflows" in the left sidebar
- Look for "Build and Deploy Docs" in the list
- Click on it to see all runs

#### Issue: No workflow runs at all

**Possible causes:**
1. Workflow file not on main branch
2. Event type mismatch
3. Permissions issue

**Solution:**
1. Commit build-docs.yml to main branch
2. Verify event types match
3. Check repository settings → Actions → General → Workflow permissions

#### Issue: Workflow triggers but fails immediately

**Check the logs for:**
- Submodule update failures
- Permission errors
- Missing dependencies

### 10. Expected Timeline

After pushing docs changes to a submodule:

```
0:00 - Push to submodule
0:10 - Submodule trigger workflow starts
0:15 - repository_dispatch event sent (HTTP 204)
0:20 - "Build and Deploy Docs" workflow starts
1:00 - Submodules updated
1:30 - Documentation built
2:00 - Pushed to gh-pages
2:05 - "pages-build-deployment" starts
2:30 - Documentation live
```

**Total time: ~2-3 minutes**

### 11. Debugging Commands

Check recent workflow runs:
```bash
# Using gh CLI
gh run list --repo soliplex/soliplex.github.io --limit 10

# Check specific run
gh run view RUN_ID --repo soliplex/soliplex.github.io
```

Check repository dispatch events (requires admin access):
```bash
# This requires GitHub Enterprise or specific permissions
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/soliplex/soliplex.github.io/events \
  | jq '.[] | select(.type == "RepositoryDispatchEvent")'
```

### 12. Still Not Working?

If the workflow still isn't triggering:

1. **Verify the workflow is committed to main:**
   ```bash
   git checkout main
   git log --oneline .github/workflows/build-docs.yml
   ```

2. **Re-trigger manually:**
   - Go to: https://github.com/soliplex/soliplex.github.io/actions
   - Click "Build and Deploy Docs"
   - Click "Run workflow"
   - Select branch: main
   - Click "Run workflow"

3. **Check GitHub Actions settings:**
   - Go to: https://github.com/soliplex/soliplex.github.io/settings/actions
   - Ensure "Allow all actions and reusable workflows" is enabled
   - Check workflow permissions

4. **Contact me with:**
   - Link to submodule workflow run (that sent the event)
   - Link to expected main workflow run (that should have been triggered)
   - Any error messages from either workflow

---

## Quick Checklist

- [ ] build-docs.yml exists on main branch
- [ ] build-docs.yml has `repository_dispatch` trigger with type `docs_update`
- [ ] Submodule workflow successfully sends event (HTTP 204)
- [ ] Token has correct permissions
- [ ] Workflow permissions configured correctly
- [ ] Checking "All workflows" in Actions tab (not just recent)
- [ ] Allowing 5-10 seconds for workflow to appear

---

**Last Updated**: 2026-01-09
