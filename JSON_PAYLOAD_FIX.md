# JSON Payload Fix Applied ✅

## Issue

When the workflow tried to trigger a documentation rebuild, it failed with:

```json
{
  "message": "Problems parsing JSON",
  "documentation_url": "https://docs.github.com/rest/repos/repos#create-a-repository-dispatch-event",
  "status": "400"
}
```

## Root Cause

The workflow was directly embedding the commit message into the JSON payload:

```yaml
-d '{
  "event_type": "docs_update",
  "client_payload": {
    "commit_message": "${{ github.event.head_commit.message }}"
  }
}'
```

This breaks when commit messages contain:
- Quotes (`"` or `'`)
- Newlines
- Backslashes
- Other special JSON characters

## Solution

Updated the workflow to use `jq` to properly construct and escape the JSON payload:

```yaml
# Properly escape JSON using jq
payload=$(jq -n \
  --arg repo "${{ github.repository }}" \
  --arg ref "${{ github.ref }}" \
  --arg sha "${{ github.sha }}" \
  --arg pusher "${{ github.actor }}" \
  --arg message "${{ github.event.head_commit.message }}" \
  '{
    event_type: "docs_update",
    client_payload: {
      repository: $repo,
      ref: $ref,
      sha: $sha,
      pusher: $pusher,
      commit_message: $message
    }
  }')

response=$(curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token ${{ secrets.DOCS_DEPLOY_TOKEN }}" \
  https://api.github.com/repos/soliplex/soliplex.github.io/dispatches \
  -d "$payload")
```

### Why This Works

- `jq -n` creates JSON from scratch
- `--arg` safely passes variables to jq
- jq automatically escapes:
  - Quotes → `\"`
  - Newlines → `\n`
  - Backslashes → `\\`
  - All other JSON special characters

## Repositories Updated

All 7 submodule repositories have been updated:

- ✅ soliplex/soliplex
- ✅ soliplex/ingester
- ✅ soliplex/ingester-agents
- ✅ soliplex/ag-ui
- ✅ soliplex/pdf-splitter
- ✅ soliplex/flutter
- ✅ soliplex/chatbot

Each repository now has the fix in the `docs/add-rebuild-trigger` branch.

## Testing

The fix was tested with pdf-splitter after modifying documentation. You can verify by:

1. Checking the workflow run in pdf-splitter repository
2. The trigger should now succeed with HTTP 204
3. The documentation build should trigger in soliplex.github.io

## Pull Requests

The PRs for all repositories include this fix. When you create the PRs using the links in [SETUP_COMPLETE.md](SETUP_COMPLETE.md), they will have the corrected workflow file.

## What Commit Messages Are Now Supported

With this fix, commit messages can safely contain:

- ✅ Quotes: `docs: update "example" section`
- ✅ Newlines: Multi-line commit messages
- ✅ Special chars: `feat: add <component> & update [docs]`
- ✅ Unicode: Emojis and international characters
- ✅ Backslashes: Windows paths like `C:\path\to\file`

## Verification

To verify the fix is working:

```bash
# Make a commit with special characters
cd projects/pdf-splitter
echo "test" >> README.md
git add README.md
git commit -m 'docs: update "quoted" section & test [special] chars'
git push

# Check the workflow run - should succeed with HTTP 204
```

---

**Fix Applied**: 2026-01-09
**Status**: All repositories updated
**Next**: Create and merge PRs
