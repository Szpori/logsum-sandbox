#!/usr/bin/env bash
set -euo pipefail

# In CI: BASE_SHA / HEAD_SHA come from the workflow env.
# Locally: compare working tree against HEAD so unstagged deletions are caught.
if [[ -n "${BASE_SHA:-}" && -n "${HEAD_SHA:-}" ]]; then
    deleted=$(git diff --name-only --diff-filter=D "$BASE_SHA" "$HEAD_SHA" -- tests/)
else
    deleted=$(git diff --name-only --diff-filter=D HEAD -- tests/)
fi

if [[ -z "$deleted" ]]; then
    echo "OK: no test files deleted."
    exit 0
fi

echo "Deleted test files detected:"
echo "$deleted"

commit_msg=$(git log -1 --format=%B)
if echo "$commit_msg" | grep -qE '^DELETE_TESTS: .+'; then
    echo "OK: DELETE_TESTS token present. Deletion approved."
    exit 0
fi

echo "FAIL: test files deleted without DELETE_TESTS: <reason> in the most recent commit message."
exit 1
