# gap-log — things the agent cannot infer from code

Each entry names something a future agent reading only the source, tests, and spec will
get wrong or not know to ask about.

---

## Gap 1 — `--min-count` flag behavior is undefined

`spec.md` reserves `--min-count` for K 5.W.7 but says nothing about its semantics.
An agent reading the spec sees a placeholder; it does not know whether the flag filters
by count ≥ N, count > N, or something else, or whether it applies before or after
normalisation. Do not implement this flag without reading the K 5.W.7 task brief first.

---

## Gap 2 — Timestamp stripping is a latent bug, not a deliberate choice

`parse_timestamp()` passes `raw` directly to `datetime.fromisoformat()` without
calling `.strip()` first. The by-hand version stripped before parsing. A CSV cell with
a leading or trailing space (`" 2024-01-01T00:00:00"`) will silently produce a WARNING
and be excluded from `first_seen`/`last_seen` in the agent-authored code. No test
covers this path in either version. If you add a test for trimmed timestamps, it will
fail on the current implementation; fix is to add `.strip()` inside `parse_timestamp`.

---

## Gap 3 — All-black-box test strategy was a kata constraint, not a style preference

The tests were authored in K 5.W.4 from `spec.md` alone — `src/logsum.py` was
intentionally not read. This is why the tests call `subprocess.run` rather than
importing and calling helpers directly. A future agent asked to add tests should match
this style (subprocess, `tmp_path`, check exit code + stderr + output CSV), not switch
to direct unit tests of internal functions, unless the task explicitly asks for that.

---

## Gap 4 — Meridian Retail naming is fictional scenario context

`checkout-service` and `cart-api` are named after a fictional e-commerce company used
throughout the bootcamp curriculum. They have no real system behind them. If you see
service names in `data/sample_events.csv` that don't match these two, they are
synthetic additions and can be treated as arbitrary strings — there is no lookup table
or external reference to consult.

---

*Last updated: 2026-08-21 (agent-replay branch, K 5.W.9)*
