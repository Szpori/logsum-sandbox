# questions.md — K 5.W.8

---

## Q1: Where is the grouping rule?

**Files read:** `spec.md`, `src/logsum.py`

**Answer:**
The grouping rule says that every input row is assigned to a bucket identified by the pair
`(normalised_level, normalised_service)`. Each unique pair produces exactly one output row.
The spec defines this rule in prose; the implementation uses a `defaultdict` keyed on that
same tuple.

**Citations:**
- `spec.md:49` — section heading "## Grouping rule"
- `spec.md:50` — "Group key: `(normalised_level, normalised_service)`."
- `spec.md:51` — "Each unique pair produces exactly one output row. Row order in output is undefined."
- `src/logsum.py:27` — `groups = defaultdict(lambda: {"count": 0, "ts_pairs": []})` — the dict that holds all groups
- `src/logsum.py:48` — `entry = groups[(level, service)]` — where the tuple key is used to look up or create a group

**Could not verify:**
- Nothing. The rule is fully specified in `spec.md` and straightforwardly implemented.

---

## Q2: How is missing level handled?

**Files read:** `spec.md`, `src/logsum.py`

**Answer:**
There are two distinct "missing level" situations with different outcomes:

1. **Empty cell** — the `level` column exists in the header but a row has no value (or only
   whitespace). The value is normalised to `UNKNOWN` and the row is included in output as
   normal. No error is raised.

2. **Missing column** — the `level` column is absent from the header entirely. This is a
   fatal error: the program prints to stderr and exits with code 1.

**Citations (empty cell path):**
- `spec.md:41-42` — normalisation rule: "`level`: strip leading/trailing whitespace; convert
  to uppercase. Empty or whitespace-only → normalise to `UNKNOWN`."
- `spec.md:70` — edge case table: "Missing `level` value (empty cell) | Normalise to
  `UNKNOWN`; include in output"
- `src/logsum.py:17-19` — `_normalise_level(value)`: strips, uppercases, returns `"UNKNOWN"`
  if the stripped string is empty
- `src/logsum.py:43` — `level = _normalise_level(row.get("level", ""))` — empty cell
  produces `""`, which flows into `_normalise_level` and becomes `"UNKNOWN"`

**Citations (missing column path):**
- `spec.md:20` — "Missing required columns are a fatal error."
- `spec.md:74` — edge case table: "Missing required column | Fatal error: print column name
  to stderr, exit 1"
- `src/logsum.py:37-40` — `missing = {"timestamp", "level", "service", "message"} - {c.strip() for c in fieldnames}` / `if missing: print(... file=sys.stderr) / sys.exit(1)`

**Could not verify:**
- Nothing. Both paths are specified in spec and implemented explicitly.

---

## Q3: How do I run tests and CI locally?

**Files read:** `CLAUDE.md`, `.github/workflows/ci.yml`

**Answer:**
Install `ruff` and `pytest` first (they are not in the standard library), then run the two
commands the CI workflow runs:

```
pip install ruff pytest
ruff check .        # lint
pytest -v           # tests
```

The CI workflow runs exactly these two commands on every push and pull request. Running them
locally reproduces the CI environment exactly (modulo Python version — CI pins 3.11).

**Citations:**
- `CLAUDE.md:16` — "`ruff` for linting"
- `CLAUDE.md:17` — "`pytest` for tests"
- `.github/workflows/ci.yml:16` — `run: pip install ruff pytest`
- `.github/workflows/ci.yml:19` — `run: ruff check .`
- `.github/workflows/ci.yml:22` — `run: pytest -v`

**Could not verify:**
- The Python version in use locally may differ from CI's `3.11`
  (`.github/workflows/ci.yml:13`). Behaviour differences between Python 3.11 and 3.12 are
  unlikely for this codebase but cannot be ruled out without testing on 3.11 explicitly.

---

## Verification

Each cited file:line opened and checked:

| Citation | Claimed content | Verdict |
|---|---|---|
| `spec.md:49` | "## Grouping rule" heading | **correct** |
| `spec.md:50` | "Group key: `(normalised_level, normalised_service)`." | **correct** |
| `spec.md:51` | "Each unique pair produces exactly one output row..." | **correct** |
| `src/logsum.py:27` | `groups = defaultdict(lambda: {"count": 0, "ts_pairs": []})` | **correct** |
| `src/logsum.py:48` | `entry = groups[(level, service)]` | **correct** |
| `spec.md:41-42` | level normalisation rule incl. UNKNOWN | **correct** — rule spans both lines |
| `spec.md:70` | edge case row for empty level cell | **correct** |
| `src/logsum.py:17-19` | `_normalise_level` function body | **correct** — 3-line function at exactly those lines |
| `src/logsum.py:43` | `level = _normalise_level(row.get("level", ""))` | **correct** |
| `spec.md:20` | "Missing required columns are a fatal error." | **correct** |
| `spec.md:74` | edge case row for missing required column | **correct** |
| `src/logsum.py:37-40` | missing-column check and `sys.exit(1)` | **correct** — check is line 37, print is 39, exit is 40 |
| `CLAUDE.md:16` | "`ruff` for linting" | **correct** |
| `CLAUDE.md:17` | "`pytest` for tests" | **correct** |
| `.github/workflows/ci.yml:16` | `run: pip install ruff pytest` | **correct** |
| `.github/workflows/ci.yml:19` | `run: ruff check .` | **correct** |
| `.github/workflows/ci.yml:22` | `run: pytest -v` | **correct** |

All 17 citations verified correct. No citation drift found.
