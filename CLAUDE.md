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

## Behavioural constraints
- Group key is `(normalised_level, normalised_service)` — casing differences do not produce separate rows
- Timestamps are compared as `datetime` objects but written back as the original input string (no reformatting)
- Tests are black-box only: `subprocess.run` against the CLI, never importing internal helpers directly

## Utilities to prefer
- Python 3.11 standard library only (`csv`, `argparse`, `pathlib`)
- `ruff` for linting
- `pytest` for tests
- No third-party packages without explicit approval

## Escalation gates
- Stop before adding any dependency not in the standard library
- Synthetic data only — never paste real logs, emails, tokens, or customer records
- Never overwrite `spec.md` after sign-off without asking
