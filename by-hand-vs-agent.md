# K 5.W.9 — By-hand vs by-agent comparison

## What both produced

Both produced a working logsum CLI that fully satisfies the base spec:
- `src/logsum.py` — grouping, normalisation, timestamp handling, fatal errors, all edge cases
- `tests/test_logsum.py` — black-box pytest tests using `tmp_path` + `subprocess.run`
- `.github/workflows/ci.yml` — ruff + pytest on push/PR (agent left it unchanged; by-hand created it in K 5.W.5)
- A provenance note recording model, context loaded, files changed, and untested items

Both passed ruff and all tests on the first run after the refactor step.

---

## Where the agent saved time

**One pass, zero iteration.** The supervised chain took 8 separate sessions across K 5.W.1–8,
each with its own branch, PR, and hand-off. The agent did the same work in a single run
without context switching.

**Refactor was built in from the start.** The by-hand implementation started as a single
`summarise()` function and arrived at decomposition only in K 5.W.6. The agent designed
with four focused helpers (`normalise_level`, `normalise_service`, `parse_timestamp`,
`read_groups`, `write_summary`) from the beginning — the "refactor" step just wrote the
doc comment describing what it had already done.

**No lint failures.** K 5.W.5 saw CI go red due to two unused imports (`os`, `pytest`).
The agent's code passed `ruff check .` immediately.

**Module-level constants.** The agent extracted `REQUIRED_COLUMNS` and `OUTPUT_HEADER` as
named constants — the by-hand version left them as inline literals. Small, but cleaner.

**Missing column error.** The agent prints one `ERROR:` line per missing column; the
by-hand version joins them all into a single comma-separated message. The agent's output
is more grep-friendly.

---

## Where the agent went wrong or shorter

**Fewer tests: 14 vs 23.** The agent covered the main spec cases but skipped several
that emerged from careful spec-reading in K 5.W.4:
- No `test_whitespace_only_level_normalises_to_unknown` (empty cell was tested, whitespace-only was not)
- No separate stderr/path-in-message tests for file-not-found
- No test for extra input columns being ignored
- No test for the two-group filter scenario (only one test per feature, not paired)

**Timestamp not stripped before parsing.** By-hand `_parse_ts` calls `value.strip()` before
`datetime.fromisoformat()`. The agent's `parse_timestamp` passes `raw` directly without
stripping. A timestamp cell with a leading space (`" 2024-01-01T00:00:00"`) would be
silently treated as malformed by the agent but parsed correctly by the by-hand version.
This is a latent bug not caught by any test in either version.

**No `row.get()` defensive access.** By-hand uses `row.get("level", "")`;
agent uses `row["level"]`. Both work because the column-presence check runs first, but
the agent relies on that guard being airtight.

---

## What the agent did better

**Architecture.** Decomposing into `read_groups()` and `write_summary()` makes each
function independently understandable and easier to unit-test if needed later. The
by-hand version only arrived there after a deliberate refactor step with a diff review.

**Type annotations.** `parse_timestamp(raw: str, row_number: int) -> datetime | None`
is more self-documenting than `_parse_ts(value, row_num)`.

**Docstrings.** The agent wrote a module docstring and function docstrings explaining
_why_ each function exists. By-hand code had minimal comments by convention.

**Untested items were honest.** The provenance note named three genuine gaps (output row
order, output path parent missing, mixed sub-second precision) — specific and accurate.

---

## What I learned about supervised vs async

**Supervised chains force checkpoints the agent skips.** Each kata step (spec, implement,
test, CI, refactor) created a natural pause where a human re-read the output before
proceeding. The agent has no equivalent pause — it produces more code faster but with
less deliberate edge-case coverage.

**The agent's refactor was cosmetic.** Because it designed cleanly from the start, the
"refactor" step just added a doc comment. The supervised chain's refactor (K 5.W.6)
was a genuine change — replacing a real smell (`if key not in groups`) with
`defaultdict`. An agent that writes clean code from the start has less to refactor,
which is good, but it means the refactor step becomes a box-tick rather than a
meaningful improvement.

**Test coverage degrades without a spec-reading pass.** K 5.W.4's constraint ("fresh
session, spec only, no reading src/") forced deliberate coverage mapping — every spec
rule got a test. The agent wrote tests reactively (one per feature it implemented) and
missed combinations and edge cases that only appear when you read the spec as a checklist.

**Citation drift is hard to delegate.** K 5.W.8 required opening every cited file:line.
The agent would produce citations but verifying them requires a human to open the files.
That step cannot be meaningfully async.

---

## What I would do differently next time

1. **Add a test-count floor to the agent prompt.** "Write at least 20 tests, covering
   every spec rule and its negation" would have closed the 14 vs 23 gap.

2. **Explicitly include a spec-checklist step.** Tell the agent: "Before writing tests,
   enumerate every spec rule as a checklist item, then confirm each has a test."

3. **Call out known subtle paths in the prompt.** The timestamp `.strip()` issue and
   the empty-cell-vs-missing-column distinction are the kinds of surprises that deserve
   an explicit mention: "Note: empty cell and missing column are different code paths."

4. **Keep the supervised chain for new domains; use the agent for replay.** When the
   problem space is unfamiliar, step-by-step builds understanding that can't be skipped.
   Once you understand the domain (as with a replay), an agent one-shot is faster and
   the quality gap is manageable with a good review.
