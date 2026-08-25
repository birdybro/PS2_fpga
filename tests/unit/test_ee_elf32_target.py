"""Directed native EE ELF32 target-policy tests."""

import pytest

from sim.loaders.elf32 import (
    ELF32_HEADER_SIZE,
    EM_MIPS,
    ET_EXEC,
    Elf32Header,
    ElfTargetError,
    parse_ee_elf32_header,
    parse_elf32_header,
    validate_ee_elf32_header,
)

IDENT_DEFAULTS = {
    0: 0x7F,
    1: ord("E"),
    2: ord("L"),
    3: ord("F"),
    4: 1,
    5: 1,
    6: 1,
    7: 0,
    8: 0,
}
FIELD_DEFAULTS = {
    "object_type": 2,
    "machine": 8,
    "header_version": 1,
    "entry": 0x0010_0000,
    "program_header_offset": ELF32_HEADER_SIZE,
    "section_header_offset": 0,
    "flags": 0x2092_4001,
    "header_size": ELF32_HEADER_SIZE,
    "program_header_entry_size": 32,
    "program_header_count": 1,
    "section_header_entry_size": 40,
    "section_header_count": 0,
    "section_name_string_table_index": 0,
}
FIELD_LAYOUT = (
    ("object_type", 2),
    ("machine", 2),
    ("header_version", 4),
    ("entry", 4),
    ("program_header_offset", 4),
    ("section_header_offset", 4),
    ("flags", 4),
    ("header_size", 2),
    ("program_header_entry_size", 2),
    ("program_header_count", 2),
    ("section_header_entry_size", 2),
    ("section_header_count", 2),
    ("section_name_string_table_index", 2),
)


def build_ee_candidate(
    *,
    byte_order: str = "little",
    ident_overrides: dict[int, int] | None = None,
    field_overrides: dict[str, int] | None = None,
) -> bytes:
    """Encode one target candidate without using the production struct layout."""
    ident = bytearray(16)
    for index, value in IDENT_DEFAULTS.items():
        ident[index] = value
    ident[5] = 1 if byte_order == "little" else 2
    if ident_overrides is not None:
        for index, value in ident_overrides.items():
            ident[index] = value

    values = FIELD_DEFAULTS | (field_overrides or {})
    fields = b"".join(
        values[field].to_bytes(width, byteorder=byte_order, signed=False)
        for field, width in FIELD_LAYOUT
    )
    return bytes(ident) + fields


@pytest.mark.unit
def test_parse_ee_elf32_header_accepts_native_executable_target() -> None:
    """Accept little-endian ET_EXEC with the generic EM_MIPS assignment."""
    header = parse_ee_elf32_header(build_ee_candidate())
    assert isinstance(header, Elf32Header)
    assert header.object_type == ET_EXEC
    assert header.machine == EM_MIPS
    assert header.byte_order == "little"


@pytest.mark.unit
def test_validate_ee_elf32_header_returns_same_immutable_record() -> None:
    """Apply target policy without copying or mutating the parsed record."""
    header = parse_elf32_header(build_ee_candidate())
    assert validate_ee_elf32_header(header) is header


@pytest.mark.unit
@pytest.mark.parametrize("object_type", (0, 1, 3, 4, 0xFF00))
def test_parse_ee_elf32_header_rejects_non_executable_type(object_type: int) -> None:
    """Reject generic object types that cannot be directly started by the harness."""
    image = build_ee_candidate(field_overrides={"object_type": object_type})
    with pytest.raises(ElfTargetError, match="ET_EXEC"):
        parse_ee_elf32_header(image)


@pytest.mark.unit
@pytest.mark.parametrize("machine", (0, 3, 10, 62, 0xFFFF))
def test_parse_ee_elf32_header_rejects_non_mips_machine(machine: int) -> None:
    """Reject no-machine, x86, legacy MIPS-LE, x86-64, and reserved targets."""
    image = build_ee_candidate(field_overrides={"machine": machine})
    with pytest.raises(ElfTargetError, match="EM_MIPS"):
        parse_ee_elf32_header(image)


@pytest.mark.unit
def test_parse_ee_elf32_header_rejects_big_endian_mips() -> None:
    """Reject a correctly decoded generic big-endian EM_MIPS executable."""
    image = build_ee_candidate(byte_order="big")
    with pytest.raises(ElfTargetError, match="little-endian"):
        parse_ee_elf32_header(image)


@pytest.mark.unit
def test_validate_ee_elf32_header_does_not_invent_osabi_or_flag_policy() -> None:
    """Leave unresearched OSABI and processor-flag restrictions to later evidence."""
    image = build_ee_candidate(
        ident_overrides={7: 3, 8: 7},
        field_overrides={"flags": 0xFFFF_FFFF},
    )
    header = parse_ee_elf32_header(image)
    assert (header.os_abi, header.abi_version, header.flags) == (3, 7, 0xFFFF_FFFF)


@pytest.mark.unit
def test_validate_ee_elf32_header_requires_parsed_record() -> None:
    """Reject accidental raw bytes at the policy-only validation boundary."""
    with pytest.raises(TypeError, match="Elf32Header"):
        validate_ee_elf32_header(build_ee_candidate())  # type: ignore[arg-type]
