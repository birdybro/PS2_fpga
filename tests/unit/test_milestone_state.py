"""Directed tests for persistent milestone-state validation."""

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from scripts.check_milestones import validate_milestones, validate_progress

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_state() -> dict:
    """Load a fresh copy of the repository milestone state."""
    return yaml.safe_load((REPO_ROOT / "milestones.yaml").read_text(encoding="utf-8"))


@pytest.mark.unit
def test_repository_milestone_and_progress_state_is_valid() -> None:
    """Keep the committed machine and human resume state synchronized."""
    state = load_state()
    progress = (REPO_ROOT / "PROGRESS.md").read_text(encoding="utf-8")

    assert validate_milestones(state) == []
    assert validate_progress(state, progress) == []


@pytest.mark.unit
def test_active_milestone_rejects_incomplete_dependency() -> None:
    """Do not allow work to become active before its dependency is complete."""
    state = deepcopy(load_state())
    active = next(item for item in state["milestones"] if item["status"] == "active")
    dependency_id = active["dependencies"][0]
    dependency = next(item for item in state["milestones"] if item["id"] == dependency_id)
    dependency["status"] = "pending"
    dependency["commit"] = None

    errors = validate_milestones(state)
    assert any("incomplete dependencies" in error for error in errors)


@pytest.mark.unit
def test_progress_rejects_mismatched_active_milestone() -> None:
    """Ensure a stale human resume pointer cannot pass state validation."""
    state = load_state()
    progress = (REPO_ROOT / "PROGRESS.md").read_text(encoding="utf-8")
    active_id = next(item["id"] for item in state["milestones"] if item["status"] == "active")
    progress = progress.replace(f"Next milestone: {active_id}", "Next milestone: M999")

    errors = validate_progress(state, progress)
    assert errors == ["PROGRESS.md next milestone does not match the active milestone"]
