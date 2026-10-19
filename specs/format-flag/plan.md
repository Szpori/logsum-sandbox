# Implementation plan — `--format` flag

Input: `specs/format-flag/spec.md` (signed off 2026-08-30)

---

## Component 1 — Argument layer (`main()`, argparse block)

Adds `--format {csv,json}` as an optional argument with default `"csv"`. Validates the value
before any file I/O: if unrecognised, prints `ERROR: unsupported format: <value>` to stderr
and exits 1. No other component sees an invalid format string.

**Interface 1 → 2:** `args.format: str` — always `"csv"` or `"json"` at this point; all
invalid values are already rejected with exit 1.

---

## Component 2 — Dispatch layer (`main()`, post-read block)

After `read_groups()` returns, inspects `args.format` and calls either the existing CSV writer
or the new JSON writer. Catches `OSError` from either writer, prints `ERROR: <msg>` to stderr,
and exits 1.

**Interface 2 → CSV writer:** existing `write_summary(groups: dict, output_path: Path) -> None`;
raises `OSError` on write failure, propagates to the dispatch layer.

**Interface 2 → JSON writer:** new `write_json_summary(groups: dict, output_path: Path) -> None`;
same signature as `write_summary`; raises `OSError` on write failure, propagates to the dispatch
layer.

---

## Component 3 — CSV writer (existing — `write_summary`)

No changes. Serialises `groups` to a comma-separated file; `count` is written as a string by
`csv.writer`. Included here to make the dispatch interface explicit.

---

## Component 4 — JSON writer (new — `write_json_summary`)

Serialises `groups` to a JSON array, one object per group. `count` is emitted as a JSON
integer. `first_seen` and `last_seen` are the original input strings of the chronologically
earliest/latest parseable timestamps; empty string when none exist. Writes with
`json.dumps(..., ensure_ascii=False)` and a trailing newline.

---

## Component 5 — Tests (black-box CLI, `tests/test_logsum.py`)

All new tests use `subprocess.run` + `tmp_path`, consistent with the existing suite. New tests
cover: invalid format exits 1; omitted/`csv`/`json` each produce the correct output shape;
`count` is JSON integer; empty timestamps; out-of-order timestamps; header-only input with
`--format json` produces `[]`.
