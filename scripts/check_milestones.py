#!/usr/bin/env python3
"""Validate milestone schema, dependencies, and human-readable resume state."""

import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MILESTONES_PATH = REPO_ROOT / "milestones.yaml"
PROGRESS_PATH = REPO_ROOT / "PROGRESS.md"
ALLOWED_STATES = {"pending", "active", "blocked", "complete"}
REQUIRED_FIELDS = {
    "id",
    "title",
    "subsystem",
    "status",
    "dependencies",
    "tests",
    "references",
    "commit",
    "notes",
}
PROGRESS_FIELDS = {
    "Last completed milestone",
    "Next milestone",
    "Current subsystem",
    "Current regression status",
    "Known architectural inaccuracies",
    "Known timing inaccuracies",
    "External blockers",
    "Most recent pushed commit",
}
MILESTONE_ID = re.compile(r"^M\d{3}[A-Z]?$")
COMMIT_ID = re.compile(r"^[0-9a-f]{7,40}$")


def _validate_entry(index: int, milestone: Any) -> tuple[list[str], str | None]:
    """Validate one milestone's required fields and scalar/list types."""
    errors: list[str] = []
    location = f"milestones[{index}]"
    if not isinstance(milestone, dict):
        return [f"{location} must be a mapping"], None
    missing = REQUIRED_FIELDS - milestone.keys()
    if missing:
        return [f"{location} is missing fields: {', '.join(sorted(missing))}"], None
    milestone_id = milestone["id"]
    if not isinstance(milestone_id, str) or not MILESTONE_ID.fullmatch(milestone_id):
        return [f"{location}.id is invalid: {milestone_id!r}"], None
    if milestone["status"] not in ALLOWED_STATES:
        errors.append(f"{milestone_id} has invalid status {milestone['status']!r}")
    for field in ("title", "subsystem", "notes"):
        if not isinstance(milestone[field], str) or not milestone[field].strip():
            errors.append(f"{milestone_id}.{field} must be a nonempty string")
    for field in ("dependencies", "tests", "references"):
        values = milestone[field]
        if not isinstance(values, list) or (field != "dependencies" and not values):
            errors.append(f"{milestone_id}.{field} must be a nonempty list")
        elif not all(isinstance(value, str) and value.strip() for value in values):
            errors.append(f"{milestone_id}.{field} contains an invalid value")
    return errors, milestone_id


def _validate_dependencies(milestones: list[dict[str, Any]], ids: list[str]) -> list[str]:
    """Validate ordering and completion of milestone dependencies."""
    errors: list[str] = []
    positions = {milestone_id: index for index, milestone_id in enumerate(ids)}
    statuses = {
        milestone["id"]: milestone["status"]
        for milestone in milestones
        if milestone.get("id") in positions and milestone.get("status") in ALLOWED_STATES
    }
    active = [milestone_id for milestone_id, status in statuses.items() if status == "active"]
    if len(active) != 1:
        errors.append(f"exactly one milestone must be active, found {len(active)}")
    for milestone in milestones:
        milestone_id = milestone.get("id")
        dependencies = milestone.get("dependencies")
        if milestone_id not in positions or not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            if dependency not in positions:
                errors.append(f"{milestone_id} has unknown dependency {dependency}")
            elif positions[dependency] >= positions[milestone_id]:
                errors.append(f"{milestone_id} dependency {dependency} must appear earlier")
        if milestone.get("status") not in {"active", "complete"}:
            continue
        incomplete = [
            dependency for dependency in dependencies if statuses.get(dependency) != "complete"
        ]
        if incomplete:
            errors.append(f"{milestone_id} has incomplete dependencies: {', '.join(incomplete)}")
    return errors


def _validate_commits(milestones: list[dict[str, Any]], ids: list[str]) -> list[str]:
    """Validate complete and non-complete milestone commit references."""
    errors: list[str] = []
    complete_ids = [
        milestone["id"]
        for milestone in milestones
        if milestone.get("id") in ids and milestone.get("status") == "complete"
    ]
    last_complete = complete_ids[-1] if complete_ids else None
    for milestone in milestones:
        milestone_id = milestone.get("id")
        if milestone_id not in ids:
            continue
        commit = milestone.get("commit")
        if milestone.get("status") != "complete":
            if commit is not None:
                errors.append(f"{milestone_id} non-complete milestone commit must be null")
            continue
        if not isinstance(commit, str):
            errors.append(f"{milestone_id} complete milestone requires a commit")
        elif not COMMIT_ID.fullmatch(commit) and not commit.startswith("self ("):
            errors.append(f"{milestone_id} has invalid commit {commit!r}")
        elif commit.startswith("self (") and milestone_id != last_complete:
            errors.append(f"only latest complete milestone {last_complete} may use self commit")
    return errors


def validate_milestones(data: Any) -> list[str]:
    """Return all schema and dependency errors in parsed milestone data."""
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return ["schema_version must be 1"]
    milestones = data.get("milestones")
    if not isinstance(milestones, list) or not milestones:
        return ["milestones must be a nonempty list"]

    errors: list[str] = []
    ids: list[str] = []
    for index, milestone in enumerate(milestones):
        entry_errors, milestone_id = _validate_entry(index, milestone)
        errors.extend(entry_errors)
        if milestone_id is not None:
            ids.append(milestone_id)

    duplicates = sorted(milestone_id for milestone_id, count in Counter(ids).items() if count > 1)
    if duplicates:
        errors.append(f"duplicate milestone IDs: {', '.join(duplicates)}")
    valid_mappings = [milestone for milestone in milestones if isinstance(milestone, dict)]
    errors.extend(_validate_dependencies(valid_mappings, ids))
    errors.extend(_validate_commits(valid_mappings, ids))
    return errors


def parse_progress(text: str) -> dict[str, str]:
    """Extract the required top-level resume fields from PROGRESS.md."""
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = re.fullmatch(r"- ([^:]+): (.+)", line)
        if match and match.group(1) in PROGRESS_FIELDS:
            fields[match.group(1)] = match.group(2)
    return fields


def validate_progress(data: Any, progress_text: str) -> list[str]:
    """Cross-check human-readable progress against machine-readable state."""
    errors: list[str] = []
    fields = parse_progress(progress_text)
    missing = PROGRESS_FIELDS - fields.keys()
    if missing:
        return [f"PROGRESS.md is missing fields: {', '.join(sorted(missing))}"]
    milestones = data["milestones"]
    complete = [item for item in milestones if item["status"] == "complete"]
    active = [item for item in milestones if item["status"] == "active"]
    if complete and not fields["Last completed milestone"].startswith(complete[-1]["id"]):
        errors.append("PROGRESS.md last completed milestone does not match milestones.yaml")
    if len(active) == 1 and not fields["Next milestone"].startswith(active[0]["id"]):
        errors.append("PROGRESS.md next milestone does not match the active milestone")
    if complete and not fields["Most recent pushed commit"].startswith(complete[-1]["id"]):
        errors.append("PROGRESS.md most recent pushed commit does not match latest completion")
    return errors


def main() -> int:
    data = yaml.safe_load(MILESTONES_PATH.read_text(encoding="utf-8"))
    errors = validate_milestones(data)
    errors.extend(validate_progress(data, PROGRESS_PATH.read_text(encoding="utf-8")))
    if errors:
        print("Milestone state validation failed:")
        for error in errors:
            print(f"  {error}")
        return 1
    print(f"milestone state: {len(data['milestones'])} entries, schema and resume state valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
