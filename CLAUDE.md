# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project context
Tiny CLI that reads synthetic `events.csv` logs (`timestamp`, `level`, `service`, `message`)
and writes a counted summary to `summary.csv`. No production data. Services follow Meridian
Retail naming (`checkout-service`, `cart-api`).

## Commands

```bash
# Run the CLI
python -m src.logsum data/sample_events.csv data/summary.csv

# Run all tests
pytest -v

# Run a single test
pytest tests/test_logsum.py::test_basic_grouping -v

# Lint
ruff check .
```

## Conventions
- Source code: `src/`
- Tests: `tests/`
- Data files: `data/`
- One module per concern; no circular imports

## Architecture

Single module `src/logsum.py` with four focused helpers called by `main()`:

| Function | Role |
|---|---|
| `normalise_level(raw)` | Strip + uppercase; blank → `UNKNOWN` |
| `normalise_service(raw)` | Strip + lowercase |
| `parse_timestamp(raw, row_number)` | ISO 8601 parse; warns to stderr and returns `None` on failure |
| `read_groups(reader)` | Accumulate per-`(level, service)` stats into a `defaultdict` |
| `write_summary(groups, output_path)` | Emit one CSV row per group |

Group key is `(normalised_level, normalised_service)`. Timestamps are compared as `datetime` objects for correct min/max but written back as the original input string.

All tests in `tests/test_logsum.py` are black-box CLI tests via `subprocess.run` — they invoke `python -m src.logsum` and inspect stdout/stderr/return code and the output CSV.

## Utilities to prefer
- Python 3.11 standard library only (`csv`, `argparse`, `pathlib`)
- `ruff` for linting
- `pytest` for tests
- No third-party packages without explicit approval

## Escalation gates
- Stop before adding any dependency not in the standard library
- Synthetic data only — never paste real logs, emails, tokens, or customer records
- Never overwrite `spec.md` after sign-off without asking
