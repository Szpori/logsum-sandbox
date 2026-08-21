# logsum — tech stack

## Language
Python 3.11. The `datetime | None` union syntax requires 3.10+; 3.11 is pinned to match the CI
image (`ubuntu-latest` + `actions/setup-python@v5`).

## Standard library modules in use
| Module | Role |
|---|---|
| `csv` | DictReader for input, writer for output |
| `argparse` | positional `input_csv` / `output_csv` args |
| `pathlib.Path` | file existence check, open calls |
| `collections.defaultdict` | per-group accumulator; avoids manual key-init guard |
| `datetime.datetime` | ISO 8601 parse + min/max comparison for first_seen/last_seen |
| `sys` | stderr writes, `sys.exit(1)` on fatal errors |

No framework. No third-party packages. `pip install ruff pytest` is the full install.

## Test runner
`pytest` — all tests in `tests/test_logsum.py` are black-box CLI tests via `subprocess.run`.
They exercise exit codes, stderr content, and output CSV structure. No mocking, no fixtures
beyond `tmp_path`.

## Linter / formatter
`ruff` — `ruff check .` must pass before merge (enforced by CI). Current rule violations
treated as errors: unused imports (`F401`).

## Architectural constraint
One module per concern; no circular imports. `src/logsum.py` is the sole source file.
Adding a second module requires it to have a single, named responsibility.

## Module structure — `src/logsum.py`

`main()` calls four focused helpers in order:

| Function | Role |
|---|---|
| `normalise_level(raw)` | Strip + uppercase; blank → `UNKNOWN` |
| `normalise_service(raw)` | Strip + lowercase |
| `parse_timestamp(raw, row_number)` | ISO 8601 parse; warns to stderr, returns `None` on failure |
| `read_groups(reader)` | Accumulate per-`(level, service)` stats into a `defaultdict` |
| `write_summary(groups, output_path)` | Emit one CSV row per group |
