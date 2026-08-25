"""Directed tests for the machine-readable R5900 ISA coverage contract."""

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from scripts.check_r5900_coverage import validate_r5900_coverage

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: str) -> dict:
    """Load one repository YAML document into a fresh object."""
    return yaml.safe_load((REPO_ROOT / path).read_text(encoding="utf-8"))


def validate(coverage: dict) -> list[str]:
    """Validate a coverage mutation against repository ownership and provenance state."""
    return validate_r5900_coverage(
        coverage,
        load_yaml("milestones.yaml"),
        load_yaml("references.yaml"),
    )


@pytest.mark.unit
def test_repository_r5900_foundation_coverage_is_valid() -> None:
    """Require one well-formed coverage owner for every foundation encoding."""
    assert validate(load_yaml("coverage/r5900_isa.yaml")) == []


@pytest.mark.unit
def test_r5900_coverage_rejects_missing_instruction() -> None:
    """Prevent an instruction from silently disappearing from reported coverage."""
    coverage = deepcopy(load_yaml("coverage/r5900_isa.yaml"))
    coverage["instructions"] = [
        entry for entry in coverage["instructions"] if entry["mnemonic"] != "SRA"
    ]

    errors = validate(coverage)
    assert "missing foundation instructions: SRA" in errors


@pytest.mark.unit
def test_r5900_coverage_rejects_duplicate_mnemonic() -> None:
    """Keep summary queries unambiguous by rejecting duplicate instruction rows."""
    coverage = deepcopy(load_yaml("coverage/r5900_isa.yaml"))
    coverage["instructions"].append(deepcopy(coverage["instructions"][0]))

    errors = validate(coverage)
    assert "duplicate instruction mnemonics: NOP" in errors


@pytest.mark.unit
def test_r5900_coverage_rejects_false_complete_status() -> None:
    """Do not report an unimplemented or untested instruction as complete."""
    coverage = deepcopy(load_yaml("coverage/r5900_isa.yaml"))
    coverage["instructions"][5]["status"] = "complete"

    errors = validate(coverage)
    assert "SRLV complete status requires implementation and all required tests" in errors


@pytest.mark.unit
def test_r5900_coverage_rejects_wrong_milestone_owner() -> None:
    """Keep each encoding attached to its independently gated roadmap milestone."""
    coverage = deepcopy(load_yaml("coverage/r5900_isa.yaml"))
    coverage["instructions"][1]["milestone"] = "M060"

    errors = validate(coverage)
    assert "SLL.milestone must be M058" in errors


@pytest.mark.unit
def test_r5900_coverage_rejects_unknown_reference() -> None:
    """Require every semantics claim to resolve through the provenance catalog."""
    coverage = deepcopy(load_yaml("coverage/r5900_isa.yaml"))
    coverage["instructions"][0]["references"].append("unreviewed-source")

    errors = validate(coverage)
    assert "NOP.references names unknown sources: unreviewed-source" in errors
