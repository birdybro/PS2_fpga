#!/usr/bin/env python3
"""Validate the granular Phase 1 simulation-platform roadmap."""

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MILESTONES_PATH = REPO_ROOT / "milestones.yaml"
PHASE1_ROADMAP = (
    ("M015", "Add simulation clock driver", "simulation", "M014"),
    ("M016", "Add simulation reset sequencer", "simulation", "M015"),
    ("M017", "Define internal memory transaction interface", "memory", "M016"),
    ("M018", "Assert memory transaction protocol invariants", "memory", "M017"),
    ("M019", "Add behavioral byte-addressed system RAM", "memory", "M018"),
    ("M020", "Implement aligned 32-bit RAM reads", "memory", "M019"),
    ("M021", "Implement aligned 32-bit RAM writes", "memory", "M020"),
    ("M022", "Implement RAM write byte enables", "memory", "M021"),
    ("M023", "Implement aligned 64-bit RAM reads", "memory", "M022"),
    ("M024", "Implement aligned 64-bit RAM writes", "memory", "M023"),
    ("M025", "Implement aligned 128-bit RAM reads", "memory", "M024"),
    ("M026", "Implement aligned 128-bit RAM writes", "memory", "M025"),
    ("M027", "Add configurable RAM response latency", "memory", "M026"),
    ("M028", "Add raw binary image loader", "loader", "M027"),
    ("M029", "Parse ELF32 identification and header", "loader", "M028"),
    ("M030", "Validate EE ELF machine and endianness", "loader", "M029"),
    ("M031", "Load ELF PT_LOAD segments", "loader", "M030"),
    ("M032", "Apply ELF zero-fill segments", "loader", "M031"),
    ("M033", "Publish ELF entry point", "loader", "M032"),
    ("M034", "Add simulation cycle timeout", "simulation", "M033"),
    ("M035", "Add simulation PASS termination", "simulation", "M034"),
    ("M036", "Add simulation FAIL termination", "simulation", "M035"),
    ("M037", "Add memory transaction trace", "debug", "M036"),
    ("M038", "Add architectural trace sink", "debug", "M037"),
    ("M039", "Integrate simulation waveform controls", "debug", "M038"),
    ("M040", "Assemble simulation platform top", "simulation", "M039"),
    ("M041", "Add raw binary platform integration test", "integration", "M040"),
    ("M042", "Add ELF loader and RAM integration test", "integration", "M041"),
)
NEXT_PHASE = ("M043", "Expand Phase 2 R5900 foundation roadmap", "planning", "M042")


def validate_phase1_roadmap(data: Any) -> list[str]:
    """Return ordering, title, subsystem, and dependency errors."""
    if not isinstance(data, dict) or not isinstance(data.get("milestones"), list):
        return ["milestones must be a list"]
    milestones = data["milestones"]
    indexed = {
        item.get("id"): (index, item)
        for index, item in enumerate(milestones)
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    errors: list[str] = []
    expected = (*PHASE1_ROADMAP, NEXT_PHASE)
    previous_position = -1
    for milestone_id, title, subsystem, dependency in expected:
        found = indexed.get(milestone_id)
        if found is None:
            errors.append(f"roadmap is missing {milestone_id}: {title}")
            continue
        position, milestone = found
        if position <= previous_position:
            errors.append(f"{milestone_id} is out of roadmap order")
        previous_position = position
        if milestone.get("title") != title:
            errors.append(f"{milestone_id} title must be {title!r}")
        if milestone.get("subsystem") != subsystem:
            errors.append(f"{milestone_id} subsystem must be {subsystem!r}")
        if milestone.get("dependencies") != [dependency]:
            errors.append(f"{milestone_id} must depend only on {dependency}")
    return errors


def main() -> int:
    data = yaml.safe_load(MILESTONES_PATH.read_text(encoding="utf-8"))
    errors = validate_phase1_roadmap(data)
    if errors:
        print("Phase 1 roadmap validation failed:")
        for error in errors:
            print(f"  {error}")
        return 1
    print(f"Phase 1 roadmap: {len(PHASE1_ROADMAP)} granular implementation milestones valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
