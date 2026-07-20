# logsum — Feature Spec

## Goal
Read a CSV log file (`events.csv`), group rows by normalised `level` and `service`, count each
group, and write one summary row per group to `summary.csv`.

---

## Inputs
`events.csv` — comma-separated, UTF-8, with a required header row containing exactly these
columns (order-independent):

| Column      | Type   | Notes                          |
|-------------|--------|--------------------------------|
| `timestamp` | string | ISO 8601 expected              |
| `level`     | string | e.g. INFO, WARN, ERROR, DEBUG  |
| `service`   | string | e.g. checkout-service, cart-api|
| `message`   | string | free text; not used in output  |

Extra columns are ignored. Missing required columns are a fatal error.

---

## Outputs
`summary.csv` — comma-separated, UTF-8, with header:

```
level,service,count,first_seen,last_seen
```

One row per unique `(level, service)` group after normalisation.
`first_seen` and `last_seen` are the minimum and maximum parseable timestamps in the group
(ISO 8601, as-read from input). Rows with unparseable timestamps contribute to `count` but are
excluded from `first_seen` / `last_seen` calculation.

---

## Normalisation rules
Applied before grouping:

- `level`: strip leading/trailing whitespace; convert to uppercase.
  Empty or whitespace-only → normalise to `UNKNOWN`.
- `service`: strip leading/trailing whitespace; convert to lowercase.
- `timestamp`: attempt `datetime.fromisoformat()` parse. Unparseable → emit one warning per
  offending row to stderr; row still counts toward the group.

---

## Grouping rule
Group key: `(normalised_level, normalised_service)`.
Each unique pair produces exactly one output row. Row order in output is undefined.

---

## Aggregation
Per group:

| Output field | Rule                                                      |
|--------------|-----------------------------------------------------------|
| `count`      | Number of input rows in the group (all rows, including those with unparseable timestamps) |
| `first_seen` | Minimum parseable timestamp string; empty string if none parseable |
| `last_seen`  | Maximum parseable timestamp string; empty string if none parseable |

---

## Edge cases

| Scenario                          | Behaviour                                                                 |
|-----------------------------------|---------------------------------------------------------------------------|
| Missing `level` value (empty cell)| Normalise to `UNKNOWN`; include in output                                 |
| Malformed timestamp               | Warn to stderr (`WARNING: unparseable timestamp in row N`); count the row; omit from first_seen/last_seen |
| Empty input (header row only)     | Write header-only `summary.csv`; exit 0                                   |
| Completely empty file (no header) | Fatal error: print to stderr, exit 1                                      |
| Missing required column           | Fatal error: print column name to stderr, exit 1                          |
| Input file not found              | Fatal error: print path to stderr, exit 1                                 |
| Duplicate rows                    | Each row is a separate event; no deduplication                            |

---

## CLI

```
python -m src.logsum <input_csv> <output_csv>
```

| Exit code | Meaning                            |
|-----------|------------------------------------|
| `0`       | Success                            |
| `1`       | Fatal error (file not found, missing column, empty file, unreadable input) |

No optional flags in this version. `--min-count` is reserved for K 5.W.7.

---

## Out of scope
- Filtering by date range or time window
- `--min-count` flag (K 5.W.7)
- JSON, TSV, or any non-CSV input format
- Deduplication of identical rows
- Real-time or streaming input
- Database or non-CSV output
- Log rotation or multi-file input

---

## Implementation notes
- **Timestamp comparison via parsed datetimes, output as original strings.** `first_seen` /
  `last_seen` are determined by comparing `datetime` objects, not raw strings — ensures correct
  min/max even if input has mixed sub-second precision or ordering. The original string is
  preserved in output, not a re-formatted value.
- **Surprise: empty `level` cell vs missing `level` column are different failure modes.** An
  empty cell in an existing `level` column normalises quietly to `UNKNOWN` and continues. A
  missing `level` column is a fatal error. The spec covers both but they hit different code paths
  — worth a dedicated test for each.

---

## Signed off
**Initials:** PL  
**Date:** 2026-07-20
