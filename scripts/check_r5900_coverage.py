#!/usr/bin/env python3
"""Validate the R5900 ISA coverage inventory and its milestone ownership."""

from collections import Counter
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
COVERAGE_PATH = REPO_ROOT / "coverage/r5900_isa.yaml"
MILESTONES_PATH = REPO_ROOT / "milestones.yaml"
REFERENCES_PATH = REPO_ROOT / "references.yaml"
FEATURE_STATES = ("pending", "partial", "complete")
TEST_STATES = ("pending", "complete", "not-applicable")
REQUIRED_FIELDS = {
    "mnemonic",
    "category",
    "encoding",
    "milestone",
    "decoded",
    "implemented",
    "directed_test",
    "random_differential_test",
    "exception_tests",
    "status",
    "references",
    "notes",
}
FOUNDATION_INSTRUCTIONS = (
    ("NOP", "M057"),
    ("SLL", "M058"),
    ("SRL", "M059"),
    ("SRA", "M060"),
    ("SLLV", "M061"),
    ("SRLV", "M062"),
    ("SRAV", "M063"),
    ("LUI", "M064"),
    ("ORI", "M065"),
    ("ANDI", "M066"),
    ("XORI", "M067"),
    ("ADDIU", "M068"),
    ("ADDU", "M069"),
    ("SUBU", "M070"),
    ("AND", "M071"),
    ("OR", "M072"),
    ("XOR", "M073"),
    ("NOR", "M074"),
    ("SLT", "M075"),
    ("SLTU", "M076"),
    ("SLTI", "M077"),
    ("SLTIU", "M078"),
)
INTEGER_EXTENSION_INSTRUCTIONS = (
    ("DSLL", "M085"),
    ("DSRL", "M086"),
    ("DSRA", "M087"),
    ("DSLL32", "M088"),
    ("DSRL32", "M089"),
    ("DSRA32", "M090"),
    ("DSLLV", "M091"),
    ("DSRLV", "M092"),
    ("DSRAV", "M093"),
    ("DADDIU", "M094"),
    ("DADDU", "M095"),
    ("DSUBU", "M096"),
    ("MULT", "M097"),
    ("MULTU", "M098"),
    ("DIV", "M099"),
    ("DIVU", "M100"),
    ("MFHI", "M101"),
    ("MFLO", "M102"),
    ("MTHI", "M103"),
    ("MTLO", "M104"),
    ("MULT1", "M105"),
    ("MULTU1", "M106"),
    ("DIV1", "M107"),
    ("DIVU1", "M108"),
    ("MFHI1", "M109"),
    ("MFLO1", "M110"),
    ("MTHI1", "M111"),
    ("MTLO1", "M112"),
    ("MADD", "M113"),
    ("MADDU", "M114"),
    ("MADD1", "M115"),
    ("MADDU1", "M116"),
)
INSTRUCTION_ROADMAP = (*FOUNDATION_INSTRUCTIONS, *INTEGER_EXTENSION_INSTRUCTIONS)


def _validate_text_fields(mnemonic: str, entry: dict[str, Any]) -> list[str]:
    """Validate scalar descriptive and ownership fields."""
    errors: list[str] = []
    for field in ("category", "encoding", "milestone", "notes"):
        if not isinstance(entry[field], str) or not entry[field].strip():
            errors.append(f"{mnemonic}.{field} must be a nonempty string")
    return errors


TEST_STATES_FIELDS = ("directed_test", "random_differential_test", "exception_tests")


def _validate_coverage_fields(mnemonic: str, entry: dict[str, Any]) -> list[str]:
    """Validate primitive coverage values and their local ordering."""
    errors: list[str] = []
    for field in ("decoded", "implemented"):
        if not isinstance(entry[field], bool):
            errors.append(f"{mnemonic}.{field} must be boolean")
    for field in TEST_STATES_FIELDS:
        if entry[field] not in TEST_STATES:
            errors.append(f"{mnemonic}.{field} has invalid test state {entry[field]!r}")
    if entry["status"] not in FEATURE_STATES:
        errors.append(f"{mnemonic}.status has invalid feature state {entry['status']!r}")
    if isinstance(entry["decoded"], bool) and isinstance(entry["implemented"], bool):
        if entry["implemented"] and not entry["decoded"]:
            errors.append(f"{mnemonic} cannot be implemented before it is decoded")
        completed_tests = any(entry[field] == "complete" for field in TEST_STATES_FIELDS)
        if completed_tests and not entry["implemented"]:
            errors.append(f"{mnemonic} cannot complete tests before implementation")
        errors.extend(_validate_status(mnemonic, entry))
    return errors


def _validate_entry_references(mnemonic: str, entry: dict[str, Any]) -> list[str]:
    """Validate the local reference-list shape before catalog resolution."""
    references = entry["references"]
    if not isinstance(references, list) or not references:
        return [f"{mnemonic}.references must be a nonempty list"]
    if not all(isinstance(reference, str) and reference for reference in references):
        return [f"{mnemonic}.references contains an invalid value"]
    if len(references) != len(set(references)):
        return [f"{mnemonic}.references contains duplicates"]
    return []


def _validate_entry(index: int, entry: Any) -> tuple[list[str], str | None]:
    """Validate the shape and local state consistency of one instruction."""
    location = f"instructions[{index}]"
    if not isinstance(entry, dict):
        return [f"{location} must be a mapping"], None
    missing = REQUIRED_FIELDS - entry.keys()
    if missing:
        return [f"{location} is missing fields: {', '.join(sorted(missing))}"], None
    mnemonic = entry["mnemonic"]
    if not isinstance(mnemonic, str) or not mnemonic or mnemonic != mnemonic.upper():
        return [f"{location}.mnemonic must be a nonempty uppercase string"], None
    errors = _validate_text_fields(mnemonic, entry)
    errors.extend(_validate_coverage_fields(mnemonic, entry))
    errors.extend(_validate_entry_references(mnemonic, entry))
    return errors, mnemonic


def _validate_status(mnemonic: str, entry: dict[str, Any]) -> list[str]:
    """Require summary status to agree with the individual coverage fields."""
    errors: list[str] = []
    tests = [entry[field] for field in TEST_STATES_FIELDS]
    progressed = (
        entry["decoded"] or entry["implemented"] or any(state != "pending" for state in tests)
    )
    complete = (
        entry["decoded"]
        and entry["implemented"]
        and entry["directed_test"] == "complete"
        and entry["random_differential_test"] == "complete"
        and entry["exception_tests"] in {"complete", "not-applicable"}
    )
    if entry["status"] == "pending" and progressed:
        errors.append(f"{mnemonic} pending status cannot contain completed coverage")
    elif entry["status"] == "partial" and not progressed:
        errors.append(f"{mnemonic} partial status requires some completed coverage")
    elif entry["status"] == "partial" and complete:
        errors.append(f"{mnemonic} fully covered entry must have complete status")
    elif entry["status"] == "complete" and not complete:
        errors.append(f"{mnemonic} complete status requires implementation and all required tests")
    return errors


def _known_ids(data: Any, collection: str, id_field: str) -> set[str]:
    """Return valid string identifiers from a supporting state file."""
    if not isinstance(data, dict) or not isinstance(data.get(collection), list):
        return set()
    return {
        item[id_field]
        for item in data[collection]
        if isinstance(item, dict) and isinstance(item.get(id_field), str)
    }


def _validate_metadata(data: dict[str, Any]) -> list[str]:
    """Validate coverage document identity and its published state vocabulary."""
    errors: list[str] = []
    if data.get("architecture") != "r5900":
        errors.append("architecture must be r5900")
    if data.get("scope") != "scalar-functional-roadmap":
        errors.append("scope must be scalar-functional-roadmap")
    states = data.get("coverage_states")
    if states != {"feature": list(FEATURE_STATES), "test": list(TEST_STATES)}:
        errors.append("coverage_states must publish the validator's feature and test states")
    return errors


def _validate_inventory(mnemonics: list[str]) -> list[str]:
    """Validate exact scalar-roadmap membership and order."""
    errors: list[str] = []
    duplicates = sorted(name for name, count in Counter(mnemonics).items() if count > 1)
    if duplicates:
        errors.append(f"duplicate instruction mnemonics: {', '.join(duplicates)}")
    foundation_names = [mnemonic for mnemonic, _ in FOUNDATION_INSTRUCTIONS]
    extension_names = [mnemonic for mnemonic, _ in INTEGER_EXTENSION_INSTRUCTIONS]
    expected_names = [mnemonic for mnemonic, _ in INSTRUCTION_ROADMAP]
    missing_foundation = [name for name in foundation_names if name not in mnemonics]
    missing_extension = [name for name in extension_names if name not in mnemonics]
    unexpected = [mnemonic for mnemonic in mnemonics if mnemonic not in expected_names]
    if missing_foundation:
        errors.append(f"missing foundation instructions: {', '.join(missing_foundation)}")
    if missing_extension:
        errors.append(f"missing integer extension instructions: {', '.join(missing_extension)}")
    if unexpected:
        errors.append(f"unexpected scalar roadmap instructions: {', '.join(unexpected)}")
    if (
        not missing_foundation
        and not missing_extension
        and not unexpected
        and mnemonics != expected_names
    ):
        errors.append("scalar roadmap instructions are out of roadmap order")
    return errors


def _validate_ownership(
    entries: list[dict[str, Any]], milestones: Any, references: Any
) -> list[str]:
    """Resolve instruction owners and source identifiers against project state."""
    errors: list[str] = []
    milestone_ids = _known_ids(milestones, "milestones", "id")
    reference_ids = _known_ids(references, "references", "id")
    entries_by_name = {entry.get("mnemonic"): entry for entry in entries}
    for mnemonic, expected_milestone in INSTRUCTION_ROADMAP:
        entry = entries_by_name.get(mnemonic)
        if entry is None:
            continue
        milestone = entry.get("milestone")
        if milestone != expected_milestone:
            errors.append(f"{mnemonic}.milestone must be {expected_milestone}")
        elif milestone not in milestone_ids:
            errors.append(f"{mnemonic}.milestone names unknown milestone {milestone}")
        entry_references = entry.get("references")
        if isinstance(entry_references, list):
            unknown = sorted(set(entry_references) - reference_ids)
            if unknown:
                errors.append(f"{mnemonic}.references names unknown sources: {', '.join(unknown)}")
    return errors


def validate_r5900_coverage(data: Any, milestones: Any, references: Any) -> list[str]:
    """Return schema, inventory, ownership, provenance, and consistency errors."""
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return ["schema_version must be 1"]
    errors = _validate_metadata(data)

    instructions = data.get("instructions")
    if not isinstance(instructions, list) or not instructions:
        return [*errors, "instructions must be a nonempty list"]
    mnemonics: list[str] = []
    valid_entries: list[dict[str, Any]] = []
    for index, entry in enumerate(instructions):
        entry_errors, mnemonic = _validate_entry(index, entry)
        errors.extend(entry_errors)
        if mnemonic is not None:
            mnemonics.append(mnemonic)
        if isinstance(entry, dict):
            valid_entries.append(entry)
    errors.extend(_validate_inventory(mnemonics))
    errors.extend(_validate_ownership(valid_entries, milestones, references))
    return errors


def main() -> int:
    coverage = yaml.safe_load(COVERAGE_PATH.read_text(encoding="utf-8"))
    milestones = yaml.safe_load(MILESTONES_PATH.read_text(encoding="utf-8"))
    references = yaml.safe_load(REFERENCES_PATH.read_text(encoding="utf-8"))
    errors = validate_r5900_coverage(coverage, milestones, references)
    if errors:
        print("R5900 coverage validation failed:")
        for error in errors:
            print(f"  {error}")
        return 1
    print(f"R5900 ISA coverage: {len(coverage['instructions'])} tracked encodings valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
