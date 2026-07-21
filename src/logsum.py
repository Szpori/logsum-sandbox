import argparse
import csv
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def _parse_ts(value, row_num):
    try:
        return datetime.fromisoformat(value.strip())
    except (ValueError, TypeError):
        print(f"WARNING: unparseable timestamp in row {row_num}", file=sys.stderr)
        return None


def _normalise_level(value):
    s = value.strip()
    return s.upper() if s else "UNKNOWN"


def _normalise_service(value):
    return value.strip().lower()


def summarise(input_path, output_path):
    groups = defaultdict(lambda: {"count": 0, "ts_pairs": []})

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        if not fieldnames:
            print(f"ERROR: empty file or missing header: {input_path}", file=sys.stderr)
            sys.exit(1)

        missing = {"timestamp", "level", "service", "message"} - {c.strip() for c in fieldnames}
        if missing:
            print(f"ERROR: missing required columns: {', '.join(sorted(missing))}", file=sys.stderr)
            sys.exit(1)

        for row_num, row in enumerate(reader, start=2):
            level = _normalise_level(row.get("level", ""))
            service = _normalise_service(row.get("service", ""))
            ts_raw = row.get("timestamp", "").strip()
            ts = _parse_ts(ts_raw, row_num)

            entry = groups[(level, service)]
            entry["count"] += 1
            if ts is not None:
                entry["ts_pairs"].append((ts, ts_raw))

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["level", "service", "count", "first_seen", "last_seen"])
        for (level, service), data in groups.items():
            pairs = data["ts_pairs"]
            first_seen = min(pairs, key=lambda x: x[0])[1] if pairs else ""
            last_seen = max(pairs, key=lambda x: x[0])[1] if pairs else ""
            writer.writerow([level, service, data["count"], first_seen, last_seen])


def main():
    parser = argparse.ArgumentParser(description="Summarise events.csv logs.")
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    args = parser.parse_args()

    if not args.input_csv.exists():
        print(f"ERROR: file not found: {args.input_csv}", file=sys.stderr)
        sys.exit(1)

    summarise(args.input_csv, args.output_csv)


if __name__ == "__main__":
    main()
