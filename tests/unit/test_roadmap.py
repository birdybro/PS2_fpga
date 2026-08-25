"""Directed tests for granular simulation-platform roadmap state."""

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from scripts.check_roadmap import (
    validate_phase1_roadmap,
    validate_phase2_foundation_roadmap,
    validate_phase2_integer_extension_roadmap,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_milestones() -> dict:
    """Load a fresh milestone database."""
    return yaml.safe_load((REPO_ROOT / "milestones.yaml").read_text(encoding="utf-8"))


@pytest.mark.unit
def test_repository_phase1_roadmap_is_complete() -> None:
    """Keep every planned simulation-platform behavior independently visible."""
    assert validate_phase1_roadmap(load_milestones()) == []


@pytest.mark.unit
def test_phase1_roadmap_rejects_missing_behavior() -> None:
    """Prevent a required access width or platform control from disappearing."""
    state = deepcopy(load_milestones())
    state["milestones"] = [item for item in state["milestones"] if item["id"] != "M025"]

    errors = validate_phase1_roadmap(state)
    assert any("roadmap is missing M025" in error for error in errors)


@pytest.mark.unit
def test_phase1_roadmap_rejects_bundled_dependency_order() -> None:
    """Keep milestones linear and independently gated rather than silently bundled."""
    state = deepcopy(load_milestones())
    milestone = next(item for item in state["milestones"] if item["id"] == "M026")
    milestone["dependencies"] = ["M024"]

    errors = validate_phase1_roadmap(state)
    assert errors == ["M026 must depend only on M025"]


@pytest.mark.unit
def test_repository_phase2_r5900_foundation_roadmap_is_complete() -> None:
    """Keep CPU state, control, each first instruction, and integration independently visible."""
    assert validate_phase2_foundation_roadmap(load_milestones()) == []


@pytest.mark.unit
def test_phase2_roadmap_rejects_missing_instruction() -> None:
    """Prevent an individual scalar instruction milestone from disappearing."""
    state = deepcopy(load_milestones())
    state["milestones"] = [item for item in state["milestones"] if item["id"] != "M060"]

    errors = validate_phase2_foundation_roadmap(state)
    assert any("roadmap is missing M060: Implement R5900 SRA" in error for error in errors)


@pytest.mark.unit
def test_phase2_roadmap_rejects_bundled_instruction_dependency() -> None:
    """Keep every instruction behind the immediately preceding green gate."""
    state = deepcopy(load_milestones())
    milestone = next(item for item in state["milestones"] if item["id"] == "M061")
    milestone["dependencies"] = ["M059"]

    errors = validate_phase2_foundation_roadmap(state)
    assert errors == ["M061 must depend only on M060"]


@pytest.mark.unit
def test_repository_phase2_r5900_integer_extension_roadmap_is_complete() -> None:
    """Keep every doubleword and dual-HI/LO behavior independently gated."""
    assert validate_phase2_integer_extension_roadmap(load_milestones()) == []


@pytest.mark.unit
def test_integer_extension_roadmap_rejects_missing_instruction() -> None:
    """Prevent a documented doubleword shift from disappearing from the plan."""
    state = deepcopy(load_milestones())
    state["milestones"] = [item for item in state["milestones"] if item["id"] != "M088"]

    errors = validate_phase2_integer_extension_roadmap(state)
    assert any("roadmap is missing M088: Implement R5900 DSLL32" in error for error in errors)


@pytest.mark.unit
def test_integer_extension_roadmap_rejects_bundled_hilo_dependency() -> None:
    """Keep the two multiply/divide paths independently reviewable."""
    state = deepcopy(load_milestones())
    milestone = next(item for item in state["milestones"] if item["id"] == "M106")
    milestone["dependencies"] = ["M104"]

    errors = validate_phase2_integer_extension_roadmap(state)
    assert errors == ["M106 must depend only on M105"]
