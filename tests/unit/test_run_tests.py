"""Directed tests for the top-level result-integrity audit."""

from pathlib import Path

import pytest

from scripts.run_tests import audit_results, record_failing_seed


@pytest.mark.unit
def test_audit_results_counts_failures_errors_and_skips(tmp_path: Path) -> None:
    """Keep every non-passing JUnit state visible to the top-level gate."""
    report = tmp_path / "results.xml"
    report.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<testsuite tests="4" failures="1" errors="1" skipped="1">
  <testcase name="pass" />
  <testcase name="fail"><failure /></testcase>
  <testcase name="error"><error /></testcase>
  <testcase name="skip"><skipped /></testcase>
</testsuite>
""",
        encoding="utf-8",
    )

    assert audit_results(report) == (4, 1, 1, 1)


@pytest.mark.unit
def test_record_failing_seed_is_append_only(tmp_path: Path) -> None:
    """Preserve every failing seed so later runs cannot erase reproduction data."""
    log_path = record_failing_seed(tmp_path, "randomized", 17)
    record_failing_seed(tmp_path, "regression", 23)

    assert log_path.read_text(encoding="utf-8").splitlines() == [
        "suite=randomized seed=17",
        "suite=regression seed=23",
    ]
