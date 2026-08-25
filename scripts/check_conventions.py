#!/usr/bin/env python3
"""Enforce repository coding, verification, and accuracy conventions."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONVENTIONS_PATH = REPO_ROOT / "docs" / "CONVENTIONS.md"
KNOWN_ISSUES_PATH = REPO_ROOT / "KNOWN_ISSUES.md"
REQUIRED_HEADINGS = {
    "## RTL coding rules",
    "## Interface and reset rules",
    "## Arithmetic and data-layout rules",
    "## Assertions and accuracy annotations",
    "## Reference-model rules",
    "## Verification rules",
    "## Review and milestone gate",
}
REQUIRED_RULES = {
    "RTL-001",
    "RTL-002",
    "RTL-003",
    "RTL-004",
    "RTL-005",
    "IFC-001",
    "IFC-002",
    "IFC-003",
    "DAT-001",
    "DAT-002",
    "DAT-003",
    "AST-001",
    "AST-002",
    "AST-003",
    "REF-001",
    "REF-002",
    "REF-003",
    "VER-001",
    "VER-002",
    "VER-003",
    "VER-004",
    "VER-005",
    "GATE-001",
    "GATE-002",
    "GATE-003",
}
FORBIDDEN_TEST_PATTERNS = {
    "pytest skip": re.compile(r"\bpytest\.skip\s*\("),
    "pytest skip marker": re.compile(r"\bpytest\.mark\.skip(?:if)?\b"),
    "pytest xfail": re.compile(r"\bpytest\.(?:xfail|mark\.xfail)\b"),
    "unittest skip": re.compile(r"\bunittest\.skip\w*\b"),
    "cocotb skip": re.compile(r"@cocotb\.test\([^)]*\bskip\s*=\s*True"),
    "cocotb expected failure": re.compile(
        r"@cocotb\.test\([^)]*\bexpect_(?:fail|error)\s*=\s*True"
    ),
}
IMPLEMENTATION_ROOTS = ("rtl", "sim", "reference")


def validate_document(text: str) -> list[str]:
    """Require all normative sections and stable rule identifiers."""
    errors: list[str] = []
    headings = {line for line in text.splitlines() if line.startswith("## ")}
    missing_headings = sorted(REQUIRED_HEADINGS - headings)
    if missing_headings:
        errors.append(f"conventions are missing headings: {', '.join(missing_headings)}")
    present_rules = set(re.findall(r"\[([A-Z]+-\d{3})\]", text))
    missing_rules = sorted(REQUIRED_RULES - present_rules)
    if missing_rules:
        errors.append(f"conventions are missing rules: {', '.join(missing_rules)}")
    return errors


def validate_rtl_files(rtl_root: Path) -> list[str]:
    """Check universal source-file and implicit-net RTL rules."""
    errors: list[str] = []
    for path in sorted(rtl_root.rglob("*.sv")):
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(rtl_root.parent)
        if not text.startswith("// SPDX-License-Identifier: MIT\n"):
            errors.append(f"{relative} is missing its MIT SPDX header")
        if "`default_nettype none" not in text:
            errors.append(f"{relative} does not disable implicit nets")
        if not text.rstrip().endswith("`default_nettype wire"):
            errors.append(f"{relative} does not restore default_nettype wire")
    return errors


def validate_test_integrity(test_root: Path) -> list[str]:
    """Reject source-level mechanisms that bypass required tests."""
    errors: list[str] = []
    for path in sorted(test_root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for label, pattern in FORBIDDEN_TEST_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{path.relative_to(test_root.parent)} uses forbidden {label}")
    return errors


def validate_accuracy_annotations(root: Path, known_issues_text: str) -> list[str]:
    """Require every implementation accuracy annotation in the issue register."""
    errors: list[str] = []
    for directory in IMPLEMENTATION_ROOTS:
        for path in sorted((root / directory).rglob("*")):
            if not path.is_file() or path.suffix not in {".py", ".sv"}:
                continue
            if "TODO-ACCURACY" not in path.read_text(encoding="utf-8"):
                continue
            relative = path.relative_to(root).as_posix()
            if f"`{relative}`" not in known_issues_text:
                errors.append(f"{relative} has TODO-ACCURACY without a KNOWN_ISSUES.md entry")
    return errors


def main() -> int:
    errors = validate_document(CONVENTIONS_PATH.read_text(encoding="utf-8"))
    errors.extend(validate_rtl_files(REPO_ROOT / "rtl"))
    errors.extend(validate_test_integrity(REPO_ROOT / "tests"))
    errors.extend(
        validate_accuracy_annotations(
            REPO_ROOT,
            KNOWN_ISSUES_PATH.read_text(encoding="utf-8"),
        )
    )
    if errors:
        print("Convention validation failed:")
        for error in errors:
            print(f"  {error}")
        return 1
    print("conventions: document contract, RTL hygiene, test integrity, and accuracy valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
