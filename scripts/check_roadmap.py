#!/usr/bin/env python3
"""Validate granular simulation-platform and R5900 foundation roadmaps."""

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
PHASE2_FOUNDATION_ROADMAP = (
    ("M043", "Expand Phase 2 R5900 foundation roadmap", "planning", "M042"),
    ("M044", "Establish R5900 ISA coverage matrix", "verification", "M043"),
    ("M045", "Define Python R5900 architectural state", "reference", "M044"),
    ("M046", "Define RTL R5900 architectural state types", "r5900", "M045"),
    ("M047", "Implement 128-bit R5900 GPR storage", "r5900", "M046"),
    ("M048", "Enforce immutable R5900 register zero", "r5900", "M047"),
    ("M049", "Implement R5900 program counter state", "r5900", "M048"),
    ("M050", "Define R5900 multi-cycle control states", "r5900", "M049"),
    ("M051", "Issue R5900 32-bit instruction fetch requests", "r5900", "M050"),
    ("M052", "Capture R5900 instruction fetch responses", "r5900", "M051"),
    ("M053", "Extract R5900 instruction fields", "r5900", "M052"),
    ("M054", "Add R5900 decode legality skeleton", "r5900", "M053"),
    ("M055", "Report R5900 reserved instructions", "r5900", "M054"),
    ("M056", "Add R5900 GPR writeback framework", "r5900", "M055"),
    ("M057", "Implement R5900 NOP encoding", "r5900", "M056"),
    ("M058", "Implement R5900 SLL", "r5900", "M057"),
    ("M059", "Implement R5900 SRL", "r5900", "M058"),
    ("M060", "Implement R5900 SRA", "r5900", "M059"),
    ("M061", "Implement R5900 SLLV", "r5900", "M060"),
    ("M062", "Implement R5900 SRLV", "r5900", "M061"),
    ("M063", "Implement R5900 SRAV", "r5900", "M062"),
    ("M064", "Implement R5900 LUI", "r5900", "M063"),
    ("M065", "Implement R5900 ORI", "r5900", "M064"),
    ("M066", "Implement R5900 ANDI", "r5900", "M065"),
    ("M067", "Implement R5900 XORI", "r5900", "M066"),
    ("M068", "Implement R5900 ADDIU", "r5900", "M067"),
    ("M069", "Implement R5900 ADDU", "r5900", "M068"),
    ("M070", "Implement R5900 SUBU", "r5900", "M069"),
    ("M071", "Implement R5900 AND", "r5900", "M070"),
    ("M072", "Implement R5900 OR", "r5900", "M071"),
    ("M073", "Implement R5900 XOR", "r5900", "M072"),
    ("M074", "Implement R5900 NOR", "r5900", "M073"),
    ("M075", "Implement R5900 SLT", "r5900", "M074"),
    ("M076", "Implement R5900 SLTU", "r5900", "M075"),
    ("M077", "Implement R5900 SLTI", "r5900", "M076"),
    ("M078", "Implement R5900 SLTIU", "r5900", "M077"),
    ("M079", "Integrate R5900 fetch with simulation RAM", "integration", "M078"),
    ("M080", "Execute a sequential R5900 NOP image", "integration", "M079"),
    ("M081", "Execute an R5900 arithmetic EE ELF", "integration", "M080"),
)
NEXT_R5900_PHASE = ("M082", "Expand R5900 64-bit integer roadmap", "planning", "M081")


def _validate_roadmap(data: Any, expected: tuple[tuple[str, str, str, str], ...]) -> list[str]:
    """Return ordering, title, subsystem, and dependency errors for one roadmap."""
    if not isinstance(data, dict) or not isinstance(data.get("milestones"), list):
        return ["milestones must be a list"]
    milestones = data["milestones"]
    indexed = {
        item.get("id"): (index, item)
        for index, item in enumerate(milestones)
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    errors: list[str] = []
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


def validate_phase1_roadmap(data: Any) -> list[str]:
    """Return ordering, title, subsystem, and dependency errors."""
    return _validate_roadmap(data, (*PHASE1_ROADMAP, PHASE2_FOUNDATION_ROADMAP[0]))


def validate_phase2_foundation_roadmap(data: Any) -> list[str]:
    """Return errors in the granular R5900 functional-foundation sequence."""
    return _validate_roadmap(data, (*PHASE2_FOUNDATION_ROADMAP, NEXT_R5900_PHASE))


def main() -> int:
    data = yaml.safe_load(MILESTONES_PATH.read_text(encoding="utf-8"))
    phase1_errors = validate_phase1_roadmap(data)
    phase2_errors = validate_phase2_foundation_roadmap(data)
    if phase1_errors or phase2_errors:
        print("Roadmap validation failed:")
        for error in (*phase1_errors, *phase2_errors):
            print(f"  {error}")
        return 1
    print(
        "roadmaps: "
        f"Phase 1 has {len(PHASE1_ROADMAP)} milestones; "
        f"R5900 foundation has {len(PHASE2_FOUNDATION_ROADMAP)} milestones"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
