"""
Black-box CLI tests for src.logsum.
All tests invoke the CLI via subprocess.run.
"""
import csv
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def run_logsum(input_path, output_path):
    return subprocess.run(
        [sys.executable, "-m", "src.logsum", str(input_path), str(output_path)],
        capture_output=True, text=True, cwd=PROJECT_ROOT, check=False,
    )

def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)

def read_rows(path):
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))

HDR = ["timestamp", "level", "service", "message"]

def test_basic_grouping(tmp_path):
    inp, out = tmp_path/"e.csv", tmp_path/"s.csv"
    write_csv(inp, [HDR,
        ["2024-01-01T10:00:00", "INFO", "checkout-service", "ok"],
        ["2024-01-01T11:00:00", "ERROR", "cart-api", "fail"]])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    rows = read_rows(out)
    assert len(rows) == 2
    keys = {(row["level"], row["service"]) for row in rows}
    assert ("INFO", "checkout-service") in keys
    assert ("ERROR", "cart-api") in keys

def test_level_uppercase(tmp_path):
    inp, out = tmp_path/"e.csv", tmp_path/"s.csv"
    write_csv(inp, [HDR, ["2024-01-01T10:00:00", "info", "svc", "m"],
                        ["2024-01-01T11:00:00", "Info", "svc", "m"]])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    rows = read_rows(out)
    assert len(rows) == 1
    assert rows[0]["level"] == "INFO"
    assert rows[0]["count"] == "2"

def test_service_lowercase(tmp_path):
    inp, out = tmp_path/"e.csv", tmp_path/"s.csv"
    write_csv(inp, [HDR, ["2024-01-01T10:00:00", "INFO", "Cart-API", "m"]])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    assert read_rows(out)[0]["service"] == "cart-api"

def test_unknown_level_empty_cell(tmp_path):
    inp, out = tmp_path/"e.csv", tmp_path/"s.csv"
    write_csv(inp, [HDR, ["2024-01-01T10:00:00", "", "svc", "m"],
                        ["2024-01-01T11:00:00", "   ", "svc", "m"]])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    rows = read_rows(out)
    assert len(rows) == 1
    assert rows[0]["level"] == "UNKNOWN"
    assert rows[0]["count"] == "2"

def test_malformed_timestamp(tmp_path):
    inp, out = tmp_path/"e.csv", tmp_path/"s.csv"
    write_csv(inp, [HDR, ["2024-01-01T10:00:00", "INFO", "svc", "good"],
                        ["not-a-date", "INFO", "svc", "bad"]])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    assert "WARNING" in r.stderr
    rows = read_rows(out)
    assert rows[0]["count"] == "2"
    assert rows[0]["first_seen"] == "2024-01-01T10:00:00"
    assert rows[0]["last_seen"] == "2024-01-01T10:00:00"

def test_header_only_input(tmp_path):
    inp, out = tmp_path/"e.csv", tmp_path/"s.csv"
    write_csv(inp, [HDR])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    assert read_rows(out) == []
    assert out.read_text(encoding="utf-8").strip() == "level,service,count,first_seen,last_seen"

def test_completely_empty_file(tmp_path):
    inp, out = tmp_path/"e.csv", tmp_path/"s.csv"
    inp.write_text("", encoding="utf-8")
    r = run_logsum(inp, out)
    assert r.returncode == 1
    assert r.stderr.strip()

def test_missing_required_column(tmp_path):
    inp, out = tmp_path/"e.csv", tmp_path/"s.csv"
    write_csv(inp, [["timestamp", "service", "message"],
                    ["2024-01-01T10:00:00", "svc", "msg"]])
    r = run_logsum(inp, out)
    assert r.returncode == 1
    assert "level" in r.stderr

def test_file_not_found(tmp_path):
    r = run_logsum(tmp_path/"nope.csv", tmp_path/"s.csv")
    assert r.returncode == 1
    assert r.stderr.strip()

def test_duplicate_rows_counted(tmp_path):
    inp, out = tmp_path/"e.csv", tmp_path/"s.csv"
    write_csv(inp, [HDR,
        ["2024-01-01T10:00:00", "INFO", "svc", "m"],
        ["2024-01-01T10:00:00", "INFO", "svc", "m"],
        ["2024-01-01T10:00:00", "INFO", "svc", "m"]])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    rows = read_rows(out)
    assert len(rows) == 1
    assert rows[0]["count"] == "3"

def test_first_last_seen(tmp_path):
    inp, out = tmp_path/"e.csv", tmp_path/"s.csv"
    write_csv(inp, [HDR,
        ["2024-03-15T12:00:00", "INFO", "svc", "mid"],
        ["2024-01-01T08:00:00", "INFO", "svc", "early"],
        ["2024-06-30T23:59:59", "INFO", "svc", "late"]])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    rows = read_rows(out)
    assert rows[0]["first_seen"] == "2024-01-01T08:00:00"
    assert rows[0]["last_seen"] == "2024-06-30T23:59:59"

def test_output_header(tmp_path):
    inp, out = tmp_path/"e.csv", tmp_path/"s.csv"
    write_csv(inp, [HDR, ["2024-01-01T10:00:00", "INFO", "svc", "m"]])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    first_line = out.read_text(encoding="utf-8").splitlines()[0]
    assert first_line == "level,service,count,first_seen,last_seen"

def test_extra_columns_ignored(tmp_path):
    inp, out = tmp_path/"e.csv", tmp_path/"s.csv"
    write_csv(inp, [["timestamp","level","service","message","extra"],
                    ["2024-01-01T10:00:00","INFO","svc","m","x"]])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    rows = read_rows(out)
    assert len(rows) == 1
    assert set(rows[0].keys()) == {"level","service","count","first_seen","last_seen"}

def test_all_bad_timestamps_empty_dates(tmp_path):
    inp, out = tmp_path/"e.csv", tmp_path/"s.csv"
    write_csv(inp, [HDR, ["bad1","INFO","svc","m"],["bad2","INFO","svc","m"]])
    r = run_logsum(inp, out)
    assert r.returncode == 0
    rows = read_rows(out)
    assert rows[0]["count"] == "2"
    assert rows[0]["first_seen"] == ""
    assert rows[0]["last_seen"] == ""
