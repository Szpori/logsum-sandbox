# Provenance note — K 5.W.7 --min-count flag

## Model used
Claude Sonnet 4.6 (claude-sonnet-4-6), running as Claude Code CLI.

## Context loaded
- `src/logsum.py` — read in full before planning and before each edit
- `spec.md` — read in full; two references to `--min-count` found (CLI section line 91, Out of scope line 97)
- `tests/test_logsum.py` — read tail to locate append point; helper pattern inspected
- Plan file at `.claude/plans/majestic-scribbling-hamster.md` — authored during plan mode, approved by user before execution

## Files changed

| File | Change summary |
|---|---|
| `src/logsum.py` | Added `min_count=1` param to `summarise()`; added `if data["count"] < min_count: continue` guard in write loop; added `--min-count N` argparse argument; passed `args.min_count` to `summarise()` |
| `spec.md` | Replaced "No optional flags" placeholder with flag table; added two edge-case rows; removed `--min-count` from Out of scope list |
| `tests/test_logsum.py` | Added `run_logsum_with_args()` helper; added 3 new tests: filter below threshold, default emits all, above-all-counts produces header-only |

## Plan deviations
None. All three steps executed exactly as planned. No extra files touched.

## Untested items
- `--min-count 0` — argparse accepts it (int), `summarise` writes all groups (every count >= 0). Behaviour is defined by the implementation but not specified in spec.md and not covered by a test.
- Non-integer values (e.g. `--min-count foo`) — argparse exits with code 2 and an error message; not tested explicitly (argparse handles this automatically).
- Very large N with empty input — not tested separately (covered implicitly by `test_header_only_exits_zero` + the new `test_min_count_above_all_counts_produces_header_only`).
