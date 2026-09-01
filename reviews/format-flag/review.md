# Review — format-flag branch (T1)
**Artefact reviewed:** `src/logsum.py` (implementation diff)
**Context (read-only):** `tests/test_format_flag_independent.py`, `tests/test_logsum.py`
**Spec:** `specs/format-flag/spec.md` (signed off 2026-08-30)

---

## Verdict: APPROVE with minor follow-up

No blocking or major findings. The implementation is spec-compliant on all six ACs,
both error paths, both boundaries, and the no-mkdir invariant. Lenses 3, 6, and 7
are clean.

Two findings require follow-up before the next feature lands on this code:

- **F2** (minor) — the duplicated timestamp-extraction block creates a divergence trap
  between the two write paths.
- **F4** (minor) — the OSError catch introduced for the CSV write path has no test,
  leaving the behaviour-change claim from F1 unverified for that arm.

F1 and F3 are documentation nits. F5 is a platform inconsistency that does not
affect correctness or test outcomes today.

---

## Findings

### Lens 1 — Behaviour Preservation

| sev | file:line | failure mode | suggested fix |
|-----|-----------|--------------|---------------|
| nit | logsum.py:7–15 | Module docstring states "Behaviour is unchanged across the refactor" but the `try/except OSError` block (lines 152–158) is new for the CSV write path: previously an unhandled OSError produced a Python traceback; now it produces `ERROR: {exc}` and exits 1 cleanly — stderr content differs even though exit code does not. | Remove or narrow the "unchanged" claim; the correct framing is "processing logic is unchanged; write-failure behaviour is now spec-compliant." |

---

### Lens 2 — Hidden Assumptions

| sev | file:line | failure mode | suggested fix |
|-----|-----------|--------------|---------------|
| minor | logsum.py:95–100 vs 82–87 | `write_json_summary` and `write_summary` each contain an identical six-line timestamp-extraction block (guard + `min` + `max` + empty-string fallback); a future bugfix applied to one and not the other silently diverges the two output paths without any test catching it. | Extract `_resolve_timestamps(stats) -> tuple[str, str]` as a private helper called by both writers; the existing tests then cover both paths through a single implementation. |
| nit | logsum.py:91–110 | `write_json_summary` documents neither its required `groups` structure (`dict[(str,str), {"count": int, "timestamps": list[tuple[datetime, str]]}]`) nor the precondition that `output_path.parent` must exist; as a non-underscore module-level function it appears public, but calling it directly (e.g. in a future unit test) will raise an uncaught `FileNotFoundError` with no guidance. | Add a one-line docstring noting the precondition, or prefix the function with `_` to signal it is an internal helper. |

---

### Lens 3 — Spec / ADR Drift

No finding for this lens — all six ACs, both §3 error paths, both §4 boundaries,
the §5 no-mkdir invariant, and the §6 exit-code table are correctly implemented.

---

### Lens 4 — Independent Tests Check

| sev | file:line | failure mode | suggested fix |
|-----|-----------|--------------|---------------|
| minor | (gap — no single line) | The `try/except OSError` wrapping `write_summary` (the CSV arm, logsum.py:156) is new behaviour introduced by this diff, but `TestWritePhaseIoFailure` only passes `--format json`; neither the `--format csv` nor the omitted-format arm is tested for write-phase I/O failure, leaving the changed CSV behaviour unverified. | Add two tests to `TestWritePhaseIoFailure` (or a new class) exercising the `--format csv` and omitted-format arms under a permission-denied output path, mirroring the existing JSON pair. |
| minor | (gap — no single line) | The duplicated timestamp logic (F2) is exercised independently for each output format but never comparatively; a divergence between `write_summary` and `write_json_summary` on the same input would not be detected because no test runs both paths on identical data and asserts equal `first_seen`/`last_seen`. | Add a parametrised test (or one explicit test) that runs the same input under both formats and compares the timestamp fields across outputs. |

---

### Lens 5 — Edge Cases

| sev | file:line | failure mode | suggested fix |
|-----|-----------|--------------|---------------|
| nit | logsum.py:108 | `write_json_summary` opens `output_path` without `newline=""`, so on Windows the trailing `\n` from `fout.write("\n")` becomes `\r\n`; `write_summary` uses `newline=""` (line 78); compact `json.dumps` is single-line so only the terminal character is affected, but the inconsistency could lead a future maintainer to copy the `newline=""` pattern incorrectly in either direction. | Add `newline=""` to `output_path.open(...)` in `write_json_summary` for platform consistency, or add a comment explaining why it is intentionally absent. |

---

### Lens 6 — Security / Tool-Call Surface

No finding for this lens — `json.dumps` escapes all user-controlled content; `--format`
is validated against a two-element whitelist before any I/O; no new subprocess, network,
or eval surface is introduced.

---

### Lens 7 — Over-engineering

No finding for this lens — every extracted function has exactly one call site; no
abstraction is present that lacks a current consumer.

---

## Summary table

| # | sev | lens | location |
|---|-----|------|----------|
| F1 | nit | behaviour preservation | logsum.py:7–15 |
| F2 | minor | hidden assumptions | logsum.py:82–87, 95–100 |
| F3 | nit | hidden assumptions | logsum.py:91 |
| F4 | minor | independent tests check | CSV write-path, no test |
| F5 | minor | independent tests check | comparative timestamp test absent |
| F6 | nit | edge cases | logsum.py:108 |

---

## Adversarial pass

*Model: claude-sonnet-4-6. Context: src/logsum.py + tests/test_format_flag_independent.py
(read-only) + F1–F6 summary. Findings below are net-new — none repeat F1–F6.*

---

### Move 1 — Pre-mortem (five root causes, most obvious → least obvious)

| # | trigger | blast radius | file:line |
|---|---------|--------------|-----------|
| C1 | Input CSV where a single `(level, service)` group spans millions of rows; all `(datetime, str)` tuples are appended to `stats["timestamps"]` but only min/max are ever used | OOM kill; no output file written; all users running logsum on large production log files | logsum.py:71 |
| C2 | Disk fills during `fout.write(json.dumps(rows, ...))` after the output file has already been truncated by `open("w")`; `OSError` is caught and exit 1 is returned, but the previous output file is now empty | Any monitoring job that diffs successive logsum outputs treats "empty file" as "service has no events" rather than "run failed"; false-clear on dashboards | logsum.py:108–109 |
| C3 | Input CSV with systematically malformed timestamps (epoch integers, locale-formatted dates, empty cells) — one `print(... file=sys.stderr)` per row; stderr pipe buffer fills (~64 KB on Linux ≈ 2 000 warning lines); for 500k malformed rows the process blocks indefinitely on the next `print` call | Process hangs silently in any pipeline where stderr is consumed (`2>&1 \| tee`, log aggregators); watchdog kills after timeout; output never written | logsum.py:49 |
| C4 | Service names embed dynamic identifiers (pod names, request IDs, tenant UUIDs); O(unique services × 4 levels) groups accumulate in `groups`; the JSON output grows proportionally | Downstream consumers with a file-size limit silently truncate or reject the output; the groups dict itself consumes unbounded memory | logsum.py:65 |
| C5 | User passes the same path for input and output (`logsum events.csv events.csv --format json`); all rows are read into `groups` (line 150), the `with` block closes the input file (line 151), then `write_json_summary` opens and truncates the same path (line 153) | Original event CSV permanently destroyed; irreversible; no warning, no `--force` guard, no `input_path != output_path` check | logsum.py:134 → 153 |

**Skipping C1** (obvious; the fix — track only running min/max — is well-known).

**Strongest from C2–C5: C3.** Directly tied to a single diff line, requires only a
routine data-quality condition (not disk-full, not user error, not cardinality explosion),
and its failure mode is a silent hang rather than a visible error — the hardest class of
incident to diagnose in a production pipeline.

---

### Move 2 — Edge-case-hunter (excluding all 42 independent-suite tests)

**Candidate A — UTF-8 BOM input file**
A CSV written by Excel or Windows Notepad with a UTF-8 BOM makes the first field name
`'﻿timestamp'` rather than `'timestamp'`. The `REQUIRED_COLUMNS` check reports
`ERROR: missing required column: timestamp` with no hint about encoding. Fix: open with
`encoding="utf-8-sig"`.
`logsum.py:144`

**Candidate B — Ragged CSV row (fewer columns than header)**
`csv.DictReader` fills missing cells with `restval=None`. A row shorter than the four-
column header sets `row["level"]` to `None`. `normalise_level(None)` calls `None.strip()`
→ **`AttributeError`**, uncaught by `except OSError`. Process exits with a Python traceback
instead of the spec-required `ERROR:` message.
`logsum.py:63` → `logsum.py:32`

**★ Candidate C — Mixed timezone-aware and timezone-naive timestamps in the same group**
`datetime.fromisoformat("2024-01-01T10:00:00")` returns a naive `datetime`;
`datetime.fromisoformat("2024-01-01T10:00:00+05:30")` returns an aware `datetime`. Both
parse successfully and are appended to `stats["timestamps"]`. When
`min(stats["timestamps"], key=lambda x: x[0])` compares them, Python raises
`TypeError: can't compare offset-naive and offset-aware datetimes`. This is not an
`OSError` and is not caught by the `except` in `main()`. The process exits with a
traceback — exit code 1 but wrong error format, violating the spec's §3 guarantee that
`ERROR:` goes to stderr. Any global service whose log sources mix UTC-offset and
naive timestamps triggers this on every run.
`logsum.py:83` (write_summary) and `logsum.py:96` (write_json_summary)

---

### Resolutions

**C3 — Unbounded WARNING output (`logsum.py:49`)**
→ **Accept with documented risk.**
This behaviour predates the diff; the refactor preserved it without change. Fixing it
requires a spec decision out of scope for this ticket (add `--quiet`, cap per-run warning
count, emit a summary line).

*Risk statement:* WARNING output from `parse_timestamp` is unbounded — one stderr write
per malformed row. In any pipeline where stderr is piped to a consumer (`2>&1 | tee`, a
log aggregator), a systematically malformed input file will fill the pipe buffer and block
the process indefinitely. Operators must redirect stderr (`2>warnings.log` or `2>/dev/null`)
until a `--max-warnings N` or `--quiet` flag is added. Revisit at next feature iteration
with SRE input on an acceptable warning budget.

---

**Candidate C — Unhandled `TypeError` from mixed-timezone group (`logsum.py:83`, `logsum.py:96`)**
→ **Fix now.**
The failure is an unhandled exception on production-plausible input that violates the
spec's §3 error-format contract. The fix is a one-liner at both sites — or, better, a
single fix inside the `_resolve_timestamps` helper that F2 already recommends extracting:

```python
try:
    first_seen = min(stats["timestamps"], key=lambda x: x[0])[1]
    last_seen  = max(stats["timestamps"], key=lambda x: x[0])[1]
except TypeError:
    first_seen = ""
    last_seen  = ""
```

Falling back to empty strings on `TypeError` is conservative and spec-safe: the spec only
guarantees chronological min/max for parseable, comparable timestamps; a mixed-timezone
group is neither.

---

### Verdict after adversarial pass

**Updated verdict: REQUEST CHANGES** (elevated from APPROVE with minor follow-up).

The elevation is driven solely by Candidate C (Move 2): an unhandled `TypeError` on
production-plausible input that exits with a traceback rather than the spec-required
`ERROR:` message. The C3 risk (WARNING flood) is accepted and documented above; it does
not change the verdict. All F1–F6 findings stand unchanged.
