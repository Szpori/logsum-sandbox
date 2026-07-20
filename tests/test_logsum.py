"""
pytest tests for logsum, derived from spec.md only.
Isolation: tmp_path fixtures for all file I/O; subprocess.run for CLI invocation.
src/logsum.py was not read when authoring these tests.
"""
import csv
import subprocess
import sys
from pathlib import Path

import pytest


# ── helpers ─────────────────────────────────────────────────────────────────────

def write_events(path: Path, rows: list, fieldnames=None) -> None:
    if fieldnames is None:
        fieldnames = ["timestamp", "level", "service", "message"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_logsum(input_path: Path, output_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "src.logsum", str(input_path), str(output_path)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )


def read_summary(path: Path) -> list:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ── 1. grouping ──────────────────────────────────────────────────────────────────

def test_same_level_service_produces_one_row(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp, [
        {"timestamp": "2024-01-01T00:00:00", "level": "INFO", "service": "cart-api", "message": "a"},
        {"timestamp": "2024-01-01T00:01:00", "level": "INFO", "service": "cart-api", "message": "b"},
        {"timestamp": "2024-01-01T00:02:00", "level": "INFO", "service": "cart-api", "message": "c"},
    ])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    rows = read_summary(out)
    assert len(rows) == 1
    assert rows[0]["count"] == "3"


def test_different_services_produce_separate_rows(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp, [
        {"timestamp": "2024-01-01T00:00:00", "level": "ERROR", "service": "cart-api", "message": ""},
        {"timestamp": "2024-01-01T00:00:00", "level": "ERROR", "service": "checkout-service", "message": ""},
    ])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    rows = read_summary(out)
    assert {row["service"] for row in rows} == {"cart-api", "checkout-service"}
    assert len(rows) == 2


# ── 2. normalisation ─────────────────────────────────────────────────────────────

def test_level_converted_to_uppercase(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp, [{"timestamp": "2024-01-01T00:00:00", "level": "info", "service": "svc", "message": ""}])
    run_logsum(inp, out)
    assert read_summary(out)[0]["level"] == "INFO"


def test_level_whitespace_stripped_and_uppercased(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp, [{"timestamp": "2024-01-01T00:00:00", "level": "  warn  ", "service": "svc", "message": ""}])
    run_logsum(inp, out)
    assert read_summary(out)[0]["level"] == "WARN"


def test_service_converted_to_lowercase(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp, [{"timestamp": "2024-01-01T00:00:00", "level": "INFO", "service": "CART-API", "message": ""}])
    run_logsum(inp, out)
    assert read_summary(out)[0]["service"] == "cart-api"


# ── 3. missing level value (empty cell) → UNKNOWN — different path from missing column ──

def test_empty_level_cell_normalises_to_unknown(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp, [{"timestamp": "2024-01-01T00:00:00", "level": "", "service": "svc", "message": ""}])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    assert read_summary(out)[0]["level"] == "UNKNOWN"


def test_whitespace_only_level_normalises_to_unknown(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp, [{"timestamp": "2024-01-01T00:00:00", "level": "   ", "service": "svc", "message": ""}])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    assert read_summary(out)[0]["level"] == "UNKNOWN"


# ── 4. malformed timestamp ────────────────────────────────────────────────────────

def test_malformed_timestamp_warns_to_stderr(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp, [{"timestamp": "not-a-date", "level": "INFO", "service": "svc", "message": ""}])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    assert "WARNING" in r.stderr


def test_malformed_timestamp_row_still_counted(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp, [
        {"timestamp": "not-a-date", "level": "INFO", "service": "svc", "message": ""},
        {"timestamp": "also-bad",   "level": "INFO", "service": "svc", "message": ""},
    ])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    assert read_summary(out)[0]["count"] == "2"


def test_malformed_timestamp_excluded_from_first_last_seen(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp, [{"timestamp": "not-a-date", "level": "INFO", "service": "svc", "message": ""}])
    run_logsum(inp, out)
    row = read_summary(out)[0]
    assert row["first_seen"] == ""
    assert row["last_seen"] == ""


def test_malformed_timestamp_mixed_with_valid(tmp_path):
    """Bad-ts rows count; first/last_seen come only from valid timestamps."""
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp, [
        {"timestamp": "2024-01-01T10:00:00", "level": "INFO", "service": "svc", "message": ""},
        {"timestamp": "not-a-date",           "level": "INFO", "service": "svc", "message": ""},
        {"timestamp": "2024-01-01T12:00:00", "level": "INFO", "service": "svc", "message": ""},
    ])
    run_logsum(inp, out)
    row = read_summary(out)[0]
    assert row["count"] == "3"
    assert row["first_seen"] == "2024-01-01T10:00:00"
    assert row["last_seen"] == "2024-01-01T12:00:00"


# ── 5. empty input (header only) ─────────────────────────────────────────────────

def test_header_only_exits_zero(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp, [])
    assert run_logsum(inp, out).returncode == 0


def test_header_only_produces_header_only_output(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp, [])
    run_logsum(inp, out)
    assert read_summary(out) == []


# ── 6. completely empty file (no header) ─────────────────────────────────────────

def test_empty_file_exits_one(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    inp.write_text("")
    assert run_logsum(inp, out).returncode == 1


def test_empty_file_reports_error_to_stderr(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    inp.write_text("")
    r = run_logsum(inp, out)
    assert r.stderr.strip() != ""


# ── 7. missing required column → fatal, exit 1 ───────────────────────────────────

def test_missing_level_column_exits_one(tmp_path):
    """Missing 'level' column is a fatal error (different path from empty level cell)."""
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp,
                 [{"timestamp": "2024-01-01T00:00:00", "service": "svc", "message": ""}],
                 fieldnames=["timestamp", "service", "message"])
    assert run_logsum(inp, out).returncode == 1


def test_missing_required_column_mentions_column_name_in_stderr(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp,
                 [{"timestamp": "2024-01-01T00:00:00", "service": "svc", "message": ""}],
                 fieldnames=["timestamp", "service", "message"])
    r = run_logsum(inp, out)
    assert "level" in r.stderr


# ── 8. input file not found ───────────────────────────────────────────────────────

def test_missing_input_file_exits_one(tmp_path):
    out = tmp_path / "s.csv"
    assert run_logsum(tmp_path / "nonexistent.csv", out).returncode == 1


def test_missing_input_file_prints_path_to_stderr(tmp_path):
    missing = tmp_path / "nonexistent.csv"
    r = run_logsum(missing, tmp_path / "s.csv")
    assert "nonexistent.csv" in r.stderr


# ── 9. duplicate rows each counted separately ─────────────────────────────────────

def test_duplicate_rows_counted_individually(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    row = {"timestamp": "2024-01-01T00:00:00", "level": "DEBUG", "service": "svc", "message": "same"}
    write_events(inp, [row, row, row])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    assert read_summary(out)[0]["count"] == "3"


# ── 10. first_seen / last_seen are min/max of parseable timestamps ─────────────────

def test_first_seen_last_seen_are_min_max(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp, [
        {"timestamp": "2024-03-01T12:00:00", "level": "INFO", "service": "svc", "message": ""},
        {"timestamp": "2024-01-01T00:00:00", "level": "INFO", "service": "svc", "message": ""},
        {"timestamp": "2024-06-15T08:30:00", "level": "INFO", "service": "svc", "message": ""},
    ])
    run_logsum(inp, out)
    row = read_summary(out)[0]
    assert row["first_seen"] == "2024-01-01T00:00:00"
    assert row["last_seen"] == "2024-06-15T08:30:00"


# ── 11. output header is correct ──────────────────────────────────────────────────

def test_output_header_columns(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp, [{"timestamp": "2024-01-01T00:00:00", "level": "INFO", "service": "svc", "message": ""}])
    run_logsum(inp, out)
    with out.open(newline="", encoding="utf-8") as f:
        fieldnames = csv.DictReader(f).fieldnames
    assert set(fieldnames) == {"level", "service", "count", "first_seen", "last_seen"}


# ── 12. extra input columns are ignored ──────────────────────────────────────────

def test_extra_columns_in_input_are_ignored(tmp_path):
    inp, out = tmp_path / "e.csv", tmp_path / "s.csv"
    write_events(inp,
                 [{"timestamp": "2024-01-01T00:00:00", "level": "INFO", "service": "svc",
                   "message": "x", "extra_col": "ignored"}],
                 fieldnames=["timestamp", "level", "service", "message", "extra_col"])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    assert len(read_summary(out)) == 1
