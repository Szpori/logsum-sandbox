"""
logsum -- log summary CLI.

Usage:
    python -m src.logsum <input_csv> <output_csv>

REFACTOR NOTE (agent-replay):
The messiest function was a monolithic main() that mixed argument parsing,
file I/O, normalisation, timestamp parsing, and accumulation in a single
body. It was refactored into four focused helpers:
    - normalise_level() / normalise_service()  -- pure normalisation
    - parse_timestamp()                        -- parse + warn, returns datetime|None
    - read_groups()                            -- accumulation loop
    - write_summary()                          -- output formatting
Behaviour is unchanged across the refactor.
"""

import argparse
import csv
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REQUIRED_COLUMNS = {"timestamp", "level", "service", "message"}
OUTPUT_HEADER = ["level", "service", "count", "first_seen", "last_seen"]


def normalise_level(raw: str) -> str:
    """Strip whitespace and uppercase; blank values become UNKNOWN."""
    stripped = raw.strip()
    return stripped.upper() if stripped else "UNKNOWN"


def normalise_service(raw: str) -> str:
    """Strip whitespace and lowercase."""
    return raw.strip().lower()


def parse_timestamp(raw: str, row_number: int) -> datetime | None:
    """
    Parse an ISO 8601 timestamp string.
    Returns a datetime on success; warns to stderr and returns None on failure.
    """
    try:
        return datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        print(f"WARNING: unparseable timestamp in row {row_number}", file=sys.stderr)
        return None


def read_groups(reader: csv.DictReader) -> dict:
    """
    Iterate over CSV rows and accumulate per-group statistics.

    Returns a dict keyed by (normalised_level, normalised_service) where each
    value is {"count": int, "timestamps": [(datetime, original_str), ...]}.
    Row 1 is the header; data rows start at 2 for warning messages.
    """
    groups: dict = defaultdict(lambda: {"count": 0, "timestamps": []})
    for row_number, row in enumerate(reader, start=2):
        level = normalise_level(row["level"])
        service = normalise_service(row["service"])
        key = (level, service)

        groups[key]["count"] += 1

        dt = parse_timestamp(row["timestamp"], row_number)
        if dt is not None:
            groups[key]["timestamps"].append((dt, row["timestamp"]))

    return groups


def write_summary(groups: dict, output_path: Path) -> None:
    """Write a summary CSV to output_path, one row per group."""
    with output_path.open("w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)
        writer.writerow(OUTPUT_HEADER)
        for (level, service), stats in groups.items():
            if stats["timestamps"]:
                first_seen = min(stats["timestamps"], key=lambda x: x[0])[1]
                last_seen = max(stats["timestamps"], key=lambda x: x[0])[1]
            else:
                first_seen = ""
                last_seen = ""
            writer.writerow([level, service, stats["count"], first_seen, last_seen])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarise log events CSV by level and service."
    )
    parser.add_argument("input_csv", help="Path to input events CSV")
    parser.add_argument("output_csv", help="Path to output summary CSV")
    args = parser.parse_args()

    input_path = Path(args.input_csv)
    output_path = Path(args.output_csv)

    # Fatal: input file not found
    if not input_path.exists():
        print(f"ERROR: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with input_path.open(newline="", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)

        # Accessing .fieldnames triggers header read; None means no rows at all
        fieldnames = reader.fieldnames
        if not fieldnames:
            print("ERROR: input file is empty (no header)", file=sys.stderr)
            sys.exit(1)

        # Fatal: one or more required columns are absent
        missing = REQUIRED_COLUMNS - set(fieldnames)
        if missing:
            for col in sorted(missing):
                print(f"ERROR: missing required column: {col}", file=sys.stderr)
            sys.exit(1)

        groups = read_groups(reader)

    write_summary(groups, output_path)


if __name__ == "__main__":
    main()
