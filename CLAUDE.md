# logsum-sandbox

## Project context
Tiny CLI that reads synthetic `events.csv` logs (`timestamp`, `level`, `service`, `message`)
and writes a counted summary to `summary.csv`. No production data. Services follow Meridian
Retail naming (`checkout-service`, `cart-api`).

## Conventions
- Source code: `src/`
- Tests: `tests/`
- Data files: `data/`
- One module per concern; no circular imports

## Utilities to prefer
- Python 3.11 standard library only (`csv`, `argparse`, `pathlib`)
- `ruff` for linting
- `pytest` for tests
- No third-party packages without explicit approval

## Escalation gates
- Stop before adding any dependency not in the standard library
- Synthetic data only — never paste real logs, emails, tokens, or customer records
- Never overwrite `spec.md` after sign-off without asking
