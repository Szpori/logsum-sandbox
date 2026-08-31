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
