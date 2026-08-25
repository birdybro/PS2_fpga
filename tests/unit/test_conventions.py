"""Directed tests for coding and verification convention enforcement."""

from pathlib import Path

import pytest

from scripts.check_conventions import (
    validate_accuracy_annotations,
    validate_document,
    validate_rtl_files,
    validate_test_integrity,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.unit
def test_repository_conventions_are_valid() -> None:
    """Keep documentation, RTL hygiene, tests, and accuracy records compliant."""
    document = (REPO_ROOT / "docs" / "CONVENTIONS.md").read_text(encoding="utf-8")
    known_issues = (REPO_ROOT / "KNOWN_ISSUES.md").read_text(encoding="utf-8")

    assert validate_document(document) == []
    assert validate_rtl_files(REPO_ROOT / "rtl") == []
    assert validate_test_integrity(REPO_ROOT / "tests") == []
    assert validate_accuracy_annotations(REPO_ROOT, known_issues) == []


@pytest.mark.unit
def test_conventions_reject_disabled_tests(tmp_path: Path) -> None:
    """Prevent skip and expected-failure mechanisms from entering required tests."""
    tests = tmp_path / "tests"
    tests.mkdir()
    disabled_source = "pytest." + "skip('broken')\n"
    (tests / "test_disabled.py").write_text(disabled_source, encoding="utf-8")

    errors = validate_test_integrity(tests)
    assert errors == ["tests/test_disabled.py uses forbidden pytest skip"]


@pytest.mark.unit
def test_conventions_reject_unregistered_accuracy_approximation(tmp_path: Path) -> None:
    """Require implementation approximations to be visible in the issue register."""
    rtl = tmp_path / "rtl"
    rtl.mkdir()
    (rtl / "approximation.sv").write_text("// TODO-ACCURACY\n", encoding="utf-8")

    errors = validate_accuracy_annotations(tmp_path, "# Known Issues\n")
    assert errors == ["rtl/approximation.sv has TODO-ACCURACY without a KNOWN_ISSUES.md entry"]


@pytest.mark.unit
def test_conventions_reject_implicit_net_rtl(tmp_path: Path) -> None:
    """Ensure every architectural RTL file explicitly controls implicit nets."""
    rtl = tmp_path / "rtl"
    rtl.mkdir()
    (rtl / "unsafe.sv").write_text(
        "// SPDX-License-Identifier: MIT\nmodule unsafe; endmodule\n",
        encoding="utf-8",
    )

    errors = validate_rtl_files(rtl)
    assert errors == [
        "rtl/unsafe.sv does not disable implicit nets",
        "rtl/unsafe.sv does not restore default_nettype wire",
    ]
