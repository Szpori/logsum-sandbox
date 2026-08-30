"""
Black-box tests for the logsum --format flag.

All tests invoke the CLI via subprocess; no src imports.
Spec: logsum --format {csv,json} flag (signed off 2026-08-30)
"""
import csv
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import pytest

# ── Helpers ───────────────────────────────────────────────────────────────────

PYTHON = sys.executable


def run_logsum(input_path, output_path, *extra_args):
    """Invoke `python -m src.logsum <input> <output> [extra_args...]`."""
    cmd = [PYTHON, "-m", "src.logsum", str(input_path), str(output_path), *extra_args]
    return subprocess.run(cmd, capture_output=True, text=True)


def write_input_csv(path, rows):
    """
    Write a minimal log input CSV.

    # FLAG: Input column names assumed to be level, service, timestamp.
    # If the real schema uses different names (e.g. 'ts', 'datetime', 'time')
    # every call-site and the FIELDNAMES constant below must be updated.
    """
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "level", "service", "message"])
        writer.writeheader()
        writer.writerows(rows)


OUTPUT_FIELDS = {"level", "service", "count", "first_seen", "last_seen"}

# ── Shared test data ──────────────────────────────────────────────────────────

MIXED_ROWS = [
    {"level": "ERROR", "service": "auth", "timestamp": "2024-01-01T10:00:00", "message": "m"},
    {"level": "ERROR", "service": "auth", "timestamp": "2024-01-01T08:00:00", "message": "m"},
    {"level": "WARN",  "service": "api",  "timestamp": "2024-01-01T09:00:00", "message": "m"},
]

THREE_ROW_GROUP = [
    {"level": "INFO", "service": "db", "timestamp": "2024-01-01T10:00:00", "message": "m"},
    {"level": "INFO", "service": "db", "timestamp": "2024-01-01T11:00:00", "message": "m"},
    {"level": "INFO", "service": "db", "timestamp": "2024-01-01T12:00:00", "message": "m"},
]

UNPARSEABLE_ROWS = [
    {"level": "DEBUG", "service": "cache", "timestamp": "not-a-date", "message": "m"},
    {"level": "DEBUG", "service": "cache", "timestamp": "also-bad",   "message": "m"},
]

OUT_OF_ORDER_ROWS = [
    {"level": "ERROR", "service": "svc", "timestamp": "2024-01-01T10:00:00", "message": "m"},
    {"level": "ERROR", "service": "svc", "timestamp": "2024-01-01T08:00:00", "message": "m"},
    {"level": "ERROR", "service": "svc", "timestamp": "2024-01-01T12:00:00", "message": "m"},
]


# ── AC-1: --format omitted → CSV with correct header ─────────────────────────

class TestFormatOmitted:
    def test_output_is_csv_with_correct_header(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.csv"
        write_input_csv(inp, MIXED_ROWS)
        result = run_logsum(inp, out)
        assert result.returncode == 0
        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert set(reader.fieldnames) == OUTPUT_FIELDS

    def test_output_file_is_created(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.csv"
        write_input_csv(inp, MIXED_ROWS)
        result = run_logsum(inp, out)
        assert result.returncode == 0
        assert out.exists()

    def test_omitted_produces_same_output_as_format_csv(self, tmp_path):
        """Default behaviour must be identical to --format csv."""
        inp = tmp_path / "input.csv"
        out_implicit = tmp_path / "implicit.csv"
        out_explicit = tmp_path / "explicit.csv"
        write_input_csv(inp, MIXED_ROWS)
        r1 = run_logsum(inp, out_implicit)
        r2 = run_logsum(inp, out_explicit, "--format", "csv")
        assert r1.returncode == 0
        assert r2.returncode == 0
        assert out_implicit.read_text(encoding="utf-8") == out_explicit.read_text(encoding="utf-8")


# ── AC-2: --format csv → CSV with correct header ─────────────────────────────

class TestFormatCsv:
    def test_output_is_csv_with_correct_header(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.csv"
        write_input_csv(inp, MIXED_ROWS)
        result = run_logsum(inp, out, "--format", "csv")
        assert result.returncode == 0
        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert set(reader.fieldnames) == OUTPUT_FIELDS

    def test_exit_code_is_zero(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.csv"
        write_input_csv(inp, MIXED_ROWS)
        result = run_logsum(inp, out, "--format", "csv")
        assert result.returncode == 0

    def test_every_row_has_exactly_the_five_fields(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.csv"
        write_input_csv(inp, MIXED_ROWS)
        run_logsum(inp, out, "--format", "csv")
        with open(out, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) > 0
        for row in rows:
            assert set(row.keys()) == OUTPUT_FIELDS

    def test_output_is_not_json(self, tmp_path):
        """CSV output must not be valid JSON."""
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.csv"
        write_input_csv(inp, MIXED_ROWS)
        run_logsum(inp, out, "--format", "csv")
        content = out.read_text(encoding="utf-8").strip()
        with pytest.raises((json.JSONDecodeError, ValueError)):
            json.loads(content)


# ── AC-3: --format json → JSON array with exactly five keys ──────────────────

class TestFormatJson:
    def test_output_is_a_json_array(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        write_input_csv(inp, MIXED_ROWS)
        result = run_logsum(inp, out, "--format", "json")
        assert result.returncode == 0
        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data, list)

    def test_each_element_has_exactly_five_keys(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        write_input_csv(inp, MIXED_ROWS)
        run_logsum(inp, out, "--format", "json")
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) > 0
        for obj in data:
            assert set(obj.keys()) == OUTPUT_FIELDS

    def test_no_extra_keys_in_any_element(self, tmp_path):
        """Negative: no element may have keys outside the five specified."""
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        write_input_csv(inp, MIXED_ROWS)
        run_logsum(inp, out, "--format", "json")
        data = json.loads(out.read_text(encoding="utf-8"))
        for obj in data:
            extra = set(obj.keys()) - OUTPUT_FIELDS
            assert extra == set(), f"Unexpected keys: {extra}"

    def test_output_is_not_csv_format(self, tmp_path):
        """JSON output must not start with a CSV header line."""
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        write_input_csv(inp, MIXED_ROWS)
        run_logsum(inp, out, "--format", "json")
        content = out.read_text(encoding="utf-8").strip()
        assert not content.startswith("level,service,count")


# ── AC-4: count field is a JSON integer, not a string ────────────────────────

class TestJsonCountType:
    def test_count_is_integer_three_for_three_row_group(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        write_input_csv(inp, THREE_ROW_GROUP)
        run_logsum(inp, out, "--format", "json")
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) == 1, "Expected exactly one group (INFO/db)"
        assert isinstance(data[0]["count"], int)
        assert data[0]["count"] == 3

    def test_count_is_not_a_string(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        write_input_csv(inp, THREE_ROW_GROUP)
        run_logsum(inp, out, "--format", "json")
        data = json.loads(out.read_text(encoding="utf-8"))
        assert not isinstance(data[0]["count"], str)

    def test_count_one_for_single_row_group(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        write_input_csv(inp, [{"level": "INFO", "service": "solo", "timestamp": "2024-01-01T00:00:00", "message": "m"}])
        run_logsum(inp, out, "--format", "json")
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert isinstance(data[0]["count"], int)
        assert data[0]["count"] == 1

    def test_raw_json_count_is_not_quoted(self, tmp_path):
        """The serialised JSON bytes must not contain `"count": "3"` (quoted)."""
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        write_input_csv(inp, THREE_ROW_GROUP)
        run_logsum(inp, out, "--format", "json")
        raw = out.read_text(encoding="utf-8")
        # Any form of "count":"3" or "count": "3" means count is a string
        assert '"count": "3"' not in raw
        assert '"count":"3"' not in raw


# ── AC-5: all-unparseable timestamps → empty-string first_seen / last_seen ───

class TestUnparseableTimestamps:
    def test_both_fields_are_empty_string_when_all_unparseable(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        write_input_csv(inp, UNPARSEABLE_ROWS)
        result = run_logsum(inp, out, "--format", "json")
        assert result.returncode == 0
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["first_seen"] == ""
        assert data[0]["last_seen"] == ""

    def test_empty_timestamp_cell_is_unparseable(self, tmp_path):
        """
        datetime.fromisoformat('') raises ValueError → treated as malformed.
        # FLAG: If the real timestamp column name differs, this test needs
        # updating; the fromisoformat contract is solid but the field name is not.
        """
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        write_input_csv(inp, [{"level": "INFO", "service": "s", "timestamp": "", "message": "m"}])
        run_logsum(inp, out, "--format", "json")
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data[0]["first_seen"] == ""
        assert data[0]["last_seen"] == ""

    def test_mixed_group_uses_only_parseable_timestamps(self, tmp_path):
        """
        When some rows are parseable and some are not, the parseable ones
        determine first_seen / last_seen; malformed rows are ignored.
        # FLAG: Spec only specifies empty-string for *all-unparseable* groups.
        # The mixed case is inferred from the fromisoformat contract; this
        # test encodes the most natural interpretation.
        """
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        rows = [
            {"level": "WARN", "service": "svc", "timestamp": "not-a-date",          "message": "m"},
            {"level": "WARN", "service": "svc", "timestamp": "2024-06-01T12:00:00", "message": "m"},
        ]
        write_input_csv(inp, rows)
        run_logsum(inp, out, "--format", "json")
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["first_seen"] == "2024-06-01T12:00:00"
        assert data[0]["last_seen"] == "2024-06-01T12:00:00"

    def test_none_value_in_timestamp_cell(self, tmp_path):
        """
        datetime.fromisoformat raises TypeError on None → treated as malformed.
        # FLAG: Whether csv.DictReader ever yields None (vs empty string) for
        # a missing cell is implementation-dependent; this guards that path.
        """
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        # Write a row with a completely missing timestamp cell value
        with open(inp, "w", newline="", encoding="utf-8") as f:
            f.write("level,service,timestamp,message\n")
            f.write("ERROR,svc,,\n")  # empty cell → fromisoformat('') raises ValueError
        run_logsum(inp, out, "--format", "json")
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data[0]["first_seen"] == ""
        assert data[0]["last_seen"] == ""


# ── AC-6: out-of-order timestamps → chronological min/max ────────────────────

class TestOutOfOrderTimestamps:
    def test_first_seen_is_chronological_minimum(self, tmp_path):
        """08:00 row arrives second in input but must be first_seen."""
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        write_input_csv(inp, OUT_OF_ORDER_ROWS)
        run_logsum(inp, out, "--format", "json")
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert "08:00:00" in data[0]["first_seen"]

    def test_last_seen_is_chronological_maximum(self, tmp_path):
        """12:00 row arrives last in input and is also the max — both must hold."""
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        write_input_csv(inp, OUT_OF_ORDER_ROWS)
        run_logsum(inp, out, "--format", "json")
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "12:00:00" in data[0]["last_seen"]

    def test_first_seen_and_last_seen_are_original_input_strings(self, tmp_path):
        """Values must be the original cell strings, not normalised/reformatted."""
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        write_input_csv(inp, OUT_OF_ORDER_ROWS)
        run_logsum(inp, out, "--format", "json")
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data[0]["first_seen"] == "2024-01-01T08:00:00"
        assert data[0]["last_seen"] == "2024-01-01T12:00:00"

    def test_selection_is_not_positional(self, tmp_path):
        """Reversing the input row order must yield the same first/last values."""
        rows = [
            {"level": "INFO", "service": "s", "timestamp": "2024-01-01T10:00:00", "message": "m"},
            {"level": "INFO", "service": "s", "timestamp": "2024-01-01T08:00:00", "message": "m"},
            {"level": "INFO", "service": "s", "timestamp": "2024-01-01T12:00:00", "message": "m"},
        ]
        inp_fwd = tmp_path / "fwd.csv"
        inp_rev = tmp_path / "rev.csv"
        out_fwd = tmp_path / "out_fwd.json"
        out_rev = tmp_path / "out_rev.json"
        write_input_csv(inp_fwd, rows)
        write_input_csv(inp_rev, list(reversed(rows)))
        run_logsum(inp_fwd, out_fwd, "--format", "json")
        run_logsum(inp_rev, out_rev, "--format", "json")
        fwd = json.loads(out_fwd.read_text(encoding="utf-8"))
        rev = json.loads(out_rev.read_text(encoding="utf-8"))
        assert fwd[0]["first_seen"] == rev[0]["first_seen"]
        assert fwd[0]["last_seen"] == rev[0]["last_seen"]


# ── Section 3: Unrecognised --format value ────────────────────────────────────

class TestInvalidFormatValue:
    def test_xml_format_exits_with_code_1(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.csv"
        write_input_csv(inp, MIXED_ROWS)
        result = run_logsum(inp, out, "--format", "xml")
        assert result.returncode == 1

    def test_xml_format_prints_exact_error_to_stderr(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.csv"
        write_input_csv(inp, MIXED_ROWS)
        result = run_logsum(inp, out, "--format", "xml")
        assert "ERROR: unsupported format: xml" in result.stderr

    def test_error_fires_before_any_file_io(self, tmp_path):
        """
        Spec: exits with code 1 *before reading any input*.
        Using a non-existent input path proves the format check runs first —
        if the error message is still 'unsupported format', no I/O occurred.
        """
        inp = tmp_path / "does_not_exist.csv"
        out = tmp_path / "output.csv"
        result = run_logsum(inp, out, "--format", "xml")
        assert result.returncode == 1
        assert "ERROR: unsupported format: xml" in result.stderr
        assert not out.exists()

    def test_unrecognised_format_does_not_create_output_file(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.csv"
        write_input_csv(inp, MIXED_ROWS)
        run_logsum(inp, out, "--format", "xml")
        assert not out.exists()

    def test_other_unrecognised_values_also_error(self, tmp_path):
        """The format error must include the verbatim value in the message."""
        inp = tmp_path / "input.csv"
        write_input_csv(inp, MIXED_ROWS)
        for bad_fmt in ("yaml", "tsv", "html"):
            out = tmp_path / f"output_{bad_fmt}"
            result = run_logsum(inp, out, "--format", bad_fmt)
            assert result.returncode == 1, f"Expected exit 1 for --format {bad_fmt}"
            assert f"ERROR: unsupported format: {bad_fmt}" in result.stderr

    def test_format_value_is_case_sensitive(self, tmp_path):
        """
        # FLAG: Spec lists {csv,json} in lowercase. 'JSON' and 'CSV' are not
        # listed and are therefore unrecognised values; this test encodes
        # the strict reading. If the implementation accepts them, update the
        # assertion to returncode == 0.
        """
        inp = tmp_path / "input.csv"
        write_input_csv(inp, MIXED_ROWS)
        for bad_fmt in ("JSON", "CSV"):
            out = tmp_path / f"out_{bad_fmt}"
            result = run_logsum(inp, out, "--format", bad_fmt)
            assert result.returncode == 1
            assert f"ERROR: unsupported format: {bad_fmt}" in result.stderr

    def test_nothing_written_to_stdout_on_format_error(self, tmp_path):
        """Error must go to stderr only; stdout should be empty."""
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.csv"
        write_input_csv(inp, MIXED_ROWS)
        result = run_logsum(inp, out, "--format", "xml")
        assert result.stdout.strip() == ""


# ── Section 3: Write-phase I/O failure ───────────────────────────────────────

class TestWritePhaseIoFailure:
    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="chmod read-only semantics are unreliable on Windows; "
               "use icacls-based tests instead",
    )
    def test_permission_denied_on_output_exits_1(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        write_input_csv(inp, MIXED_ROWS)
        out.write_text("", encoding="utf-8")
        os.chmod(out, 0o444)
        try:
            result = run_logsum(inp, out, "--format", "json")
            assert result.returncode == 1
        finally:
            os.chmod(out, 0o644)

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="chmod read-only semantics are unreliable on Windows",
    )
    def test_permission_denied_prints_error_to_stderr(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        write_input_csv(inp, MIXED_ROWS)
        out.write_text("", encoding="utf-8")
        os.chmod(out, 0o444)
        try:
            result = run_logsum(inp, out, "--format", "json")
            assert "ERROR" in result.stderr
        finally:
            os.chmod(out, 0o644)


# ── Section 4: Empty input (header only) ─────────────────────────────────────

class TestEmptyInput:
    def _write_header_only(self, path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "level", "service", "message"])
            writer.writeheader()

    def test_json_format_outputs_empty_array(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        self._write_header_only(inp)
        result = run_logsum(inp, out, "--format", "json")
        assert result.returncode == 0
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data == []

    def test_json_output_is_exactly_empty_array_literal(self, tmp_path):
        """
        Spec says 'the output file contains exactly []'.
        # FLAG: The spec wording 'exactly []' is ambiguous about trailing
        # whitespace or newlines. This test normalises with strip(); if the
        # spec means literally two bytes '[' ']' with no newline, change to
        # `out.read_text().rstrip('\\n') == '[]'` or an exact byte check.
        """
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.json"
        self._write_header_only(inp)
        run_logsum(inp, out, "--format", "json")
        assert out.read_text(encoding="utf-8").strip() == "[]"

    def test_csv_format_with_empty_input_outputs_header_only(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.csv"
        self._write_header_only(inp)
        result = run_logsum(inp, out, "--format", "csv")
        assert result.returncode == 0
        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert set(reader.fieldnames) == OUTPUT_FIELDS
            assert list(reader) == []

    def test_omitted_format_with_empty_input_exits_0(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "output.csv"
        self._write_header_only(inp)
        result = run_logsum(inp, out)
        assert result.returncode == 0


# ── Section 4: Output path with missing parent directory ─────────────────────

class TestMissingOutputParentDirectory:
    def test_exits_1_when_parent_dir_missing(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "nonexistent_dir" / "output.json"
        write_input_csv(inp, MIXED_ROWS)
        result = run_logsum(inp, out, "--format", "json")
        assert result.returncode == 1

    def test_prints_error_to_stderr_when_parent_dir_missing(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "nonexistent_dir" / "output.json"
        write_input_csv(inp, MIXED_ROWS)
        result = run_logsum(inp, out, "--format", "json")
        assert result.stderr.strip() != ""

    def test_does_not_create_missing_parent_directory(self, tmp_path):
        """Spec: the CLI never calls mkdir."""
        inp = tmp_path / "input.csv"
        missing_dir = tmp_path / "nonexistent_dir"
        out = missing_dir / "output.json"
        write_input_csv(inp, MIXED_ROWS)
        run_logsum(inp, out, "--format", "json")
        assert not missing_dir.exists()

    def test_missing_parent_applies_to_csv_format(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "nodir" / "output.csv"
        write_input_csv(inp, MIXED_ROWS)
        result = run_logsum(inp, out, "--format", "csv")
        assert result.returncode == 1

    def test_missing_parent_applies_to_omitted_format(self, tmp_path):
        inp = tmp_path / "input.csv"
        out = tmp_path / "nodir" / "output.csv"
        write_input_csv(inp, MIXED_ROWS)
        result = run_logsum(inp, out)
        assert result.returncode == 1


# ── Section 6: NFR — JSON latency ≤ 2× CSV latency at 10 000 rows ────────────

@pytest.mark.slow
class TestJsonLatencyBudget:
    """
    NFR: JSON output must complete within 2× the wall-clock time of CSV
    output for the same 10 000-row input.

    # FLAG: Wall-clock timing is inherently flaky under CI load. Consider
    # running with -m slow only in performance-gated pipelines, or widening
    # the multiplier to 4× for general CI to reduce false failures.
    """

    def _build_10k_input(self, path):
        levels = ["ERROR", "WARN", "INFO", "DEBUG"]
        rows = [
            {
                "level": levels[i % 4],
                "service": f"svc{i % 10}",
                "timestamp": f"2024-01-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00",
                "message": "m",
            }
            for i in range(10_000)
        ]
        write_input_csv(path, rows)

    def test_json_within_twice_csv_wall_time(self, tmp_path):
        inp = tmp_path / "big.csv"
        out_csv = tmp_path / "out.csv"
        out_json = tmp_path / "out.json"
        self._build_10k_input(inp)

        t0 = time.perf_counter()
        run_logsum(inp, out_csv, "--format", "csv")
        csv_elapsed = time.perf_counter() - t0

        t1 = time.perf_counter()
        run_logsum(inp, out_json, "--format", "json")
        json_elapsed = time.perf_counter() - t1

        assert json_elapsed <= 2 * csv_elapsed, (
            f"JSON ({json_elapsed:.3f}s) exceeded 2× CSV ({csv_elapsed:.3f}s)"
        )
