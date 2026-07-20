# Context load check — K 5.W.1

**Question asked:** "Summarise the rule file you loaded, by section, and cite the filename."

## AI response

Loaded: `CLAUDE.md` at repo root.

**Project context** — A tiny CLI that reads synthetic `events.csv` logs (`timestamp`, `level`,
`service`, `message`) and writes a counted summary to `summary.csv`. No production data; services
use Meridian Retail naming (`checkout-service`, `cart-api`).

**Conventions** — Source in `src/`, tests in `tests/`, data in `data/`. One module per concern,
no circular imports.

**Utilities to prefer** — Python 3.11 standard library only (`csv`, `argparse`, `pathlib`);
`ruff` for linting; `pytest` for tests. No third-party packages without explicit approval.

**Escalation gates** — Stop before adding any non-stdlib dependency; synthetic data only (no
real logs, emails, tokens, or customer records); never overwrite `spec.md` after sign-off
without asking.

## Verdict
`CLAUDE.md` loaded. All four sections present and cited.
