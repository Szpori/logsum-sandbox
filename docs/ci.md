# CI gates

## test-file-guard

The `test-file-guard` workflow enforces one rule on every PR against `main`: no file under
`tests/` may be deleted unless the most recent commit message on the PR branch begins with
`DELETE_TESTS: <reason>`. This matters specifically for AI-assisted PRs because a model asked
to "make the tests pass" can satisfy that instruction by deleting the failing tests rather than
fixing the code — the gate makes that path require an explicit human acknowledgement in the
commit message instead of passing silently. What the gate does not catch is weaker forms of
the same evasion: tests that are emptied, commented out, marked `@pytest.mark.skip`, or
quietly made unconditional (`assert True`). One known limitation: the commit-message check
reads only the most recent commit, so a developer who squash-rebases a `DELETE_TESTS:`
commit out of the branch history before merging can bypass the gate.

**To enforce as a required check:** GitHub → Settings → Branches → main → Branch protection
rules → Edit → "Require status checks to pass before merging" → search for and add
`check-test-deletion`.
