"""Directed generic ELF32 identification and header parser tests."""

import pytest

from sim.loaders.elf32 import ELF32_HEADER_SIZE, ElfFormatError, parse_elf32_header

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
    "program_header_offset": 0x34,
    "section_header_offset": 0x1234,
    "flags": 0x2092_4001,
    "header_size": ELF32_HEADER_SIZE,
    "program_header_entry_size": 32,
    "program_header_count": 3,
    "section_header_entry_size": 40,
    "section_header_count": 7,
    "section_name_string_table_index": 6,
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


def build_elf32_header(
    *,
    byte_order: str = "little",
    ident_overrides: dict[int, int] | None = None,
    field_overrides: dict[str, int] | None = None,
) -> bytes:
    """Build a fixture with independent integer-to-byte field encoding."""
    ident = bytearray(16)
    for index, value in IDENT_DEFAULTS.items():
        ident[index] = value
    ident[5] = 1 if byte_order == "little" else 2
    if ident_overrides is not None:
        for index, value in ident_overrides.items():
            ident[index] = value

    values = FIELD_DEFAULTS | (field_overrides or {})
    body = b"".join(
        values[field].to_bytes(width, byteorder=byte_order, signed=False)
        for field, width in FIELD_LAYOUT
    )
    return bytes(ident) + body


@pytest.mark.unit
@pytest.mark.parametrize("byte_order", ("little", "big"))
def test_parse_elf32_header_decodes_each_declared_byte_order(byte_order: str) -> None:
    """Decode every fixed field from both generic ELF data encodings."""
    image = build_elf32_header(byte_order=byte_order) + b"trailing-data"
    header = parse_elf32_header(image)
    assert header.byte_order == byte_order
    assert header.os_abi == 0
    assert header.abi_version == 0
    for field, expected in FIELD_DEFAULTS.items():
        assert getattr(header, field) == expected


@pytest.mark.unit
def test_parse_elf32_header_ignores_reserved_ident_padding() -> None:
    """Follow the generic ABI requirement that readers ignore EI_PAD bytes."""
    image = build_elf32_header(ident_overrides={9: 0xA5, 15: 0x5A})
    assert parse_elf32_header(image).entry == FIELD_DEFAULTS["entry"]


@pytest.mark.unit
@pytest.mark.parametrize("length", (0, 3, 15))
def test_parse_elf32_header_rejects_truncated_identification(length: int) -> None:
    """Reject inputs that cannot contain the complete 16-byte identification."""
    with pytest.raises(ElfFormatError, match=r"identification.*truncated"):
        parse_elf32_header(build_elf32_header()[:length])


@pytest.mark.unit
@pytest.mark.parametrize("magic_index", (0, 1, 2, 3))
def test_parse_elf32_header_rejects_each_invalid_magic_byte(magic_index: int) -> None:
    """Require all four generic ELF magic bytes independently."""
    image = build_elf32_header(ident_overrides={magic_index: 0})
    with pytest.raises(ElfFormatError, match="magic"):
        parse_elf32_header(image)


@pytest.mark.unit
@pytest.mark.parametrize("elf_class", (0, 2, 0xFF))
def test_parse_elf32_header_rejects_non_elf32_class(elf_class: int) -> None:
    """Keep ELF64 and reserved classes outside the ELF32 parser."""
    image = build_elf32_header(ident_overrides={4: elf_class})
    with pytest.raises(ElfFormatError, match="class"):
        parse_elf32_header(image)


@pytest.mark.unit
@pytest.mark.parametrize("data_encoding", (0, 3, 0xFF))
def test_parse_elf32_header_rejects_invalid_data_encoding(data_encoding: int) -> None:
    """Accept only the two generic ABI byte-order encodings at this layer."""
    image = build_elf32_header(ident_overrides={5: data_encoding})
    with pytest.raises(ElfFormatError, match="data encoding"):
        parse_elf32_header(image)


@pytest.mark.unit
@pytest.mark.parametrize("ident_version", (0, 2))
def test_parse_elf32_header_rejects_invalid_ident_version(ident_version: int) -> None:
    """Require EV_CURRENT in the independent identification version byte."""
    image = build_elf32_header(ident_overrides={6: ident_version})
    with pytest.raises(ElfFormatError, match="identification version"):
        parse_elf32_header(image)


@pytest.mark.unit
@pytest.mark.parametrize("length", (16, ELF32_HEADER_SIZE - 1))
def test_parse_elf32_header_rejects_truncated_fixed_header(length: int) -> None:
    """Reject a valid identification without all fixed ELF32 fields."""
    with pytest.raises(ElfFormatError, match=r"header.*truncated"):
        parse_elf32_header(build_elf32_header()[:length])


@pytest.mark.unit
@pytest.mark.parametrize("header_version", (0, 2))
def test_parse_elf32_header_rejects_invalid_header_version(header_version: int) -> None:
    """Require EV_CURRENT in the decoded e_version field."""
    image = build_elf32_header(field_overrides={"header_version": header_version})
    with pytest.raises(ElfFormatError, match="header version"):
        parse_elf32_header(image)


@pytest.mark.unit
@pytest.mark.parametrize("header_size", (0, ELF32_HEADER_SIZE - 1, ELF32_HEADER_SIZE + 1))
def test_parse_elf32_header_rejects_invalid_declared_size(header_size: int) -> None:
    """Require e_ehsize to describe the fixed ELF32 header layout."""
    image = build_elf32_header(field_overrides={"header_size": header_size})
    with pytest.raises(ElfFormatError, match="header size"):
        parse_elf32_header(image)


@pytest.mark.unit
@pytest.mark.parametrize("image", ("ELF", [0x7F], 0x7F45_4C46))
def test_parse_elf32_header_rejects_non_bytes_input(image: object) -> None:
    """Reject accidental paths, integer lists, and scalar magic values."""
    with pytest.raises(TypeError, match="bytes-like"):
        parse_elf32_header(image)  # type: ignore[arg-type]
