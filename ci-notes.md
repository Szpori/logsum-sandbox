# ci-notes — K 5.W.5

## Workflow

`.github/workflows/ci.yml` — triggers on `push` and `pull_request`.
Steps: checkout → setup Python 3.11 → `pip install ruff pytest` → `ruff check .` → `pytest -v`.

## Red run

**Branch:** `ci-demo`  
**Commit:** `50f56c5` — "ci-demo: introduce unused import to trigger lint failure"

Two `ruff` failures, both `F401` (imported but unused):

| File | Import | Rule |
|------|--------|------|
| `src/logsum.py:4` | `os` | F401 — planted deliberately |
| `tests/test_logsum.py:11` | `pytest` | F401 — leftover from test authoring |

## Decision

**Both were test/code bugs, not spec ambiguity.**

- `import os` in `src/logsum.py` was the deliberate violation for this kata.
- `import pytest` in `tests/test_logsum.py` was an accidental leftover — the tests use
  `tmp_path` (a built-in pytest fixture injected by the framework) and never reference
  `pytest` directly. Removing it is correct; the tests still pass.

## Green run

**Commit:** `1113155` — "fix: remove unused imports (os, pytest)"  
Both imports removed. `ruff check .` → `All checks passed!`. `pytest -v` → 23 passed.
