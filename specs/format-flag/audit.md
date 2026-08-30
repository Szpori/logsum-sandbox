# logsum `--format` flag — spec audit

Isolation tier: **A** (gaps visible from the spec text alone; no implementation or test reading required)

---

## Finding 1 — `first_seen` / `last_seen` selection criterion is undefined

**Location:** Section 1, paragraph 1 — "the original input timestamp strings"

**What is missing:** The spec never says whether "first" and "last" mean the timestamp from the
first/last row *encountered in the CSV* for that group (positional order) or the
chronologically *earliest/latest parseable timestamp value* within the group.

**Production surface:** Log files are frequently reordered by ingestion pipelines, merge jobs,
or parallel writers before they reach logsum. An implementation that uses positional order will
silently produce a `first_seen` that is chronologically later than `last_seen` whenever the
input rows for a group are out of order. No acceptance criterion in the spec covers an
out-of-order group, so both interpretations pass all listed tests.

**Disposition:** INCORPORATE — add one acceptance criterion pairing an out-of-order group with
the expected `first_seen`/`last_seen` values, and state the selection rule explicitly
(chronological min/max of parseable timestamps; positional fallback for unparseable ones if
needed).

---

## Finding 2 — "parseable timestamp" is never defined

**Location:** Section 1, paragraph 1 — "an empty string when no parseable timestamp exists"

**What is missing:** No timestamp format, standard (ISO 8601, RFC 3339), or Python parser is
named. The spec does not say whether timezone-aware strings are accepted, whether a `T`
separator is required, or whether partial dates count.

**Production surface:** `datetime.fromisoformat()` on Python < 3.11 rejects
`2024-01-01 12:00:00` (space separator); `strptime` with `%Y-%m-%dT%H:%M:%S` rejects the same
string written with a space. An implementer who picks the wrong parser silently emits `""` for
valid timestamps, corrupting `first_seen`/`last_seen` for every group in a real log file
without any error or warning.

**Disposition:** INCORPORATE — name the accepted format explicitly (the project's
`events.csv` already implies a concrete format; pin it here) and add an acceptance criterion
that drives the boundary between parseable and unparseable.

---

## Finding 3 — Exit code and output-file state for I/O errors are unspecified

**Location:** Section 3 (Errors) covers only unrecognised format; Section 6 (NFR budget)
lists only exit code 0 (success) and exit code 1 (invalid format).

**What is missing:** No exit code or output-file postcondition is specified for I/O failures
that occur *during the write phase*: disk full, permission denied on the output path, or a
write interrupted after partial output.

**Production surface:** A caller checking the exit code to decide whether to read the output
file would silently consume a truncated or invalid JSON document if the implementation exits 0
after a partial write (e.g., a swallowed `IOError`). Alternatively, an implementation that
lets the exception propagate exits 1 with a Python traceback rather than the structured error
format used for invalid-format errors — both behaviours are conforming under the current spec,
giving operators no reliable signal.

**Disposition:** INCORPORATE — extend Section 3 to cover write-phase I/O errors: exit code
(1), stderr format, and a postcondition on the output file (e.g., "partial output must not be
left at the output path on error" or explicitly acknowledging it may be left).

---

---

## Resolution summary

| Finding | Disposition | Where addressed in spec |
|---|---|---|
| 1 — selection rule | INCORPORATE | Section 1: prose + AC 6 (out-of-order group) |
| 2 — timestamp format | INCORPORATE | Section 1: `datetime.fromisoformat()` named |
| 3 — write-phase I/O | INCORPORATE | Section 3: second paragraph added |

*Audit status: signed off — 2026-08-30*
