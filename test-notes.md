# test-notes — K 5.W.4

## Isolation method

All tests use **`tmp_path`** (pytest's built-in fixture) for file I/O: each test writes its own
`events.csv` and reads back its own `summary.csv` from a throwaway temp directory. No shared
fixture files, no monkey-patching. CLI behaviour is exercised through **`subprocess.run`** so the
tests treat the program as a black box and verify exit codes + stderr as the spec defines them.

## Failure decision

**All 23 tests passed on the first run — no failures to resolve.**

The one decision worth recording came during test *design*, not at runtime:

### `test_empty_file_exits_one` vs `test_header_only_exits_zero`

The spec draws a hard line between two "empty-looking" inputs:

| Input | Expected |
|-------|----------|
| Header row only (zero data rows) | exit 0, write header-only `summary.csv` |
| Completely empty file (zero bytes) | exit 1, fatal error to stderr |

These are different spec rules, but an implementation could easily conflate them (e.g. treat
"no rows after the header" the same as "no content at all"). Having a dedicated test for each
path — rather than one parameterised test — makes the distinction explicit and ensures a future
regression on either path produces a clear, targeted failure rather than an ambiguous combined
one.

**Decision: keep as two separate tests.** The spec justifies the distinction; a single merged
test would obscure which failure mode broke.

---

*Tests authored from `spec.md` only; `src/logsum.py` was not read.*
