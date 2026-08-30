# logsum — `--format` flag spec

---

## 1. Behaviour

`--format {csv,json}` is an optional flag on the `logsum` CLI. When omitted the CLI writes
its existing comma-separated summary to the output path. When `--format json` is supplied the
CLI writes a JSON array to the output path instead, one object per group, carrying the same
five fields as a CSV row: `level` (string), `service` (string), `count` (integer),
`first_seen` (string), `last_seen` (string). `count` is serialised as a JSON integer, not a
quoted string. `first_seen` is the original input string of the chronologically earliest
parseable timestamp in the group; `last_seen` is the original input string of the
chronologically latest parseable timestamp in the group. Both are the empty string when no
parseable timestamp exists for the group. Row order in the input file does not affect which
timestamp is selected — selection is by datetime value, not by position.

A timestamp cell is parseable if Python's `datetime.fromisoformat()` accepts it without
raising `ValueError` or `TypeError`. All other values are treated as malformed.

**Acceptance criteria**

- Given a valid input CSV, When `--format` is omitted, Then the output file is a CSV with
  header row `level,service,count,first_seen,last_seen`.
- Given a valid input CSV, When `--format csv` is supplied, Then the output file is a CSV with
  header row `level,service,count,first_seen,last_seen`.
- Given a valid input CSV, When `--format json` is supplied, Then the output file contains a
  JSON array where each element is an object with exactly the keys `level`, `service`, `count`,
  `first_seen`, `last_seen`.
- Given a group with three input rows, When `--format json` is supplied, Then the `count` field
  for that group is the integer `3` (not the string `"3"`).
- Given a group whose timestamps are all unparseable, When `--format json` is supplied, Then
  `first_seen` and `last_seen` for that group are the empty string `""`.
- Given a group whose rows arrive in out-of-order timestamp sequence (e.g. 10:00, 08:00,
  12:00), When `--format json` is supplied, Then `first_seen` is `"…08:00…"` and `last_seen`
  is `"…12:00…"` (chronological min/max, not first/last row).

---

## 2. Concurrency

logsum holds no file lock; two processes writing to the same output path simultaneously produce
a corrupted or incomplete file with no error reported by either process.

---

## 3. Errors

An unrecognised `--format` value (e.g. `--format xml`) is a fatal error: the CLI prints
`ERROR: unsupported format: xml` to stderr and exits with code 1 before reading any input.

A write-phase I/O failure (e.g. permission denied on the output path) is also a fatal error:
the CLI prints an `ERROR:` message to stderr and exits with code 1. Partial output may remain
at the output path; the CLI does not guarantee cleanup.

---

## 4. Boundaries

- Given an input CSV with a header row and zero data rows, When `--format json` is supplied,
  Then the output file contains exactly `[]`.
- Given an output path whose parent directory does not exist, When the CLI is invoked with any
  `--format` value, Then the CLI exits 1 with an error message to stderr and does not create
  the missing directory.

---

## 5. Integrations

No external services. The sole filesystem assumption: the output file's parent directory exists
before the CLI is invoked; the CLI never calls `mkdir`.

---

## 6. NFR budget

| Attribute | Constraint |
|---|---|
| Latency | JSON output must complete within 2× the wall-clock time of CSV output for the same input, measured at 10 000 rows |
| Payload size | No constraint; output size is bounded by input size |
| Exit code — invalid format | `1` |
| Exit code — success | `0` |

---

*Status: signed off — 2026-08-30*
