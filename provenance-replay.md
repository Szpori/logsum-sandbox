# provenance-replay.md

## Agent-replay provenance

### Model used
claude-sonnet-4-6

### Context loaded
- C:/AI/epamFactory/curriculum-public-main/logsum-sandbox/spec.md (the only file read before writing)
- C:/AI/epamFactory/curriculum-public-main/logsum-sandbox/.github/workflows/ci.yml (read to verify existing workflow was compliant)

Files explicitly NOT read (per task constraints):
- src/logsum.py
- tests/test_logsum.py

### Files changed
| File | Action |
|------|--------|
| src/logsum.py | Overwritten -- full implementation derived from spec alone |
| tests/test_logsum.py | Overwritten -- 13 black-box pytest tests derived from spec |
| .github/workflows/ci.yml | Unchanged -- existing file already satisfies all CI requirements |
| provenance-replay.md | Created (this file) |

### Refactor applied
The function chosen for refactor was the accumulation/grouping logic that
originally would have been inlined in main(). It was extracted into:
- normalise_level() / normalise_service() -- pure one-liner helpers
- parse_timestamp() -- centralises the fromisoformat try/except + stderr warning
- read_groups() -- the accumulation loop, returns a defaultdict
- write_summary() -- output CSV formatting

This separation makes each concern independently testable and readable.
The refactor comment block is at the top of src/logsum.py.

### Deviations from spec
None. All spec requirements are implemented as written:
- Grouping by (normalised_level, normalised_service)
- Level normalisation: strip + uppercase, empty/whitespace -> UNKNOWN
- Service normalisation: strip + lowercase
- Timestamp: fromisoformat, warn on failure, omit from dates but count row
- first_seen/last_seen: datetime comparison, original string output
- Fatal errors (exit 1): file not found, missing required column, empty file
- Header-only output for header-only input (exit 0)
- No --min-count flag

### Untested items
- Output row order (spec says undefined; not tested)
- Behaviour when output_csv path does not exist (parent directory missing)
- Mixed sub-second precision timestamps (spec mentions this as motivation for
  datetime comparison vs string comparison, but no edge-case test was written)
- Windows vs Unix newline handling in output CSV
