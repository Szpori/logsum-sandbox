# Task breakdown — `--format` flag

Derived from: `specs/format-flag/plan.md`  
Constraint: each task ≤ 100-line diff, one afternoon's work, independently reviewable.

**Highest-risk task: T3.** It is the first point where T1 (arg parsing) and T2 (JSON writer)
are integrated end-to-end, adds a new OSError handler with no prior pattern in the codebase,
and carries all seven JSON-behaviour tests in one PR — any type or serialisation error surfaces
here for the first time.

---

## T1 — Add `--format` argument and validate it  ← FIRST SLICE

**Files:** `src/logsum.py`, `tests/test_logsum.py`  
**Estimated diff:** ~30 lines

**Input:** signed-off `specs/format-flag/spec.md` (Errors section, invalid-format rule)  
**Output:** `src/logsum.py` with `--format {csv,json}` accepted; `tests/test_logsum.py` with
three new tests for argument validation  
**Done:** `python -m src.logsum data/sample_events.csv /tmp/s.csv --format xml 2>&1 | grep -q "unsupported format"` exits 0 (grep found the error string)

**What changes:**
- Add `parser.add_argument("--format", choices=["csv", "json"], default="csv")` to the
  argparse block in `main()`.
- If argparse's built-in `choices=` error message does not match `ERROR: unsupported format:
  <value>`, add a custom error handler to produce the required form.

**Tests to add (3):**
- `test_format_invalid_exits_one` — `--format xml` exits 1 and stderr contains `"unsupported format"`
- `test_format_csv_accepted` — `--format csv` exits 0 and output file exists
- `test_format_json_accepted` — `--format json` exits 0 and output file exists

**ACs closed:** Errors section (invalid format); NFR exit code 1 for invalid format.

**Why first:** Additive only — one `add_argument` call, default `"csv"`, no existing test
can break. Reviewable in complete isolation.

---

## T2 — Implement `write_json_summary()`

**Files:** `src/logsum.py` only  
**Estimated diff:** ~30 lines

**Input:** `specs/format-flag/spec.md` (Behaviour section: JSON shape, count integer,
timestamp strings, empty-string rule); `docs/context/stack.md` (module structure)  
**Output:** `write_json_summary(groups: dict, output_path: Path) -> None` present in
`src/logsum.py`, immediately below `write_summary`  
**Done:** `grep "def write_json_summary" src/logsum.py` returns the function signature and
`ruff check src/logsum.py` exits 0

**What changes:**
- New function `write_json_summary(groups: dict, output_path: Path) -> None`.
- Builds a list of dicts: `count` as `int`, `first_seen`/`last_seen` as original timestamp
  strings (empty string when no parseable timestamps). Writes with
  `json.dumps(rows, ensure_ascii=False)` + trailing newline.
- `main()` is NOT yet wired to call this function — that is T3.

**Tests:** None in this task. The function cannot be reached via `subprocess.run` until T3
wires the dispatch; adding black-box tests here would require them to be skipped or would
always fail. All JSON-behaviour tests land in T3.

**ACs:** Implemented here, verified in T3 (AC 3, 4, 5, 6).

---

## T3 — Wire dispatch and add all JSON-behaviour tests  ← HIGHEST RISK

**Files:** `src/logsum.py`, `tests/test_logsum.py`  
**Estimated diff:** ~75 lines

**Input:** T1 merged (arg accepted), T2 merged (function present); `specs/format-flag/spec.md`
ACs 1–6 and Boundaries  
**Output:** `main()` dispatches to `write_json_summary` on `--format json`; seven new tests
covering all JSON behaviour  
**Done:** `python -m src.logsum data/sample_events.csv /tmp/out.json --format json && python -c "import json; rows=json.load(open('/tmp/out.json')); assert isinstance(rows[0]['count'], int)"` exits 0

**What changes:**
- Branch on `args.format` after `read_groups()`:
  `if args.format == "json": write_json_summary(groups, output_path)`
  `else: write_summary(groups, output_path)`
- Wrap both writer calls in `try/except OSError`: print `ERROR: <msg>` to stderr, exit 1.

**Tests to add (7):**
- `test_format_omitted_produces_csv` — no flag → CSV header row present
- `test_format_csv_explicit_produces_csv` — `--format csv` → CSV header row present
- `test_format_json_key_shape` — AC 3: each object has exactly the five expected keys
- `test_format_json_count_is_integer` — AC 4: count field parses as `int`
- `test_format_json_unparseable_timestamps_empty` — AC 5: all-bad timestamps → `first_seen == ""`
- `test_format_json_out_of_order_timestamps` — AC 6: rows arrive 10:00/08:00/12:00 → `first_seen` is `08:00`
- `test_format_json_empty_input_produces_empty_array` — Boundaries: header-only → `[]`

**ACs closed:** AC 1, 2, 3, 4, 5, 6; Boundaries (empty → `[]`); Errors (write-phase I/O).

---

## T4 — Update CLAUDE.md and stack.md

**Files:** `CLAUDE.md`, `docs/context/stack.md`  
**Estimated diff:** ~15 lines

**Input:** T3 merged (feature complete)  
**Output:** `CLAUDE.md` and `docs/context/stack.md` reflect the new flag and function  
**Done:** `grep "format" CLAUDE.md` shows the new behavioural constraint line

**What changes:**
- `CLAUDE.md` Behavioural constraints: add `--format {csv,json}`, default `csv`.
- `CLAUDE.md` Commands: add `--format json` example.
- `stack.md` Module structure table: add `write_json_summary` row.

**ACs closed:** none (documentation only). Safe to bundle with the T3 PR or open as follow-up.
