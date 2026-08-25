"""Directed ELF32 program-header and EE file-segment loader tests."""

from collections.abc import Mapping, Sequence

import pytest

from sim.loaders.elf32 import (
    ELF32_ADDRESS_SPACE_SIZE,
    ELF32_HEADER_SIZE,
    ELF32_PROGRAM_HEADER_SIZE,
    PT_LOAD,
    Elf32ProgramHeader,
    ElfFormatError,
    load_ee_elf32_file_segments,
    parse_elf32_program_headers,
)

HEADER_FIELD_LAYOUT = (
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
PROGRAM_HEADER_FIELD_LAYOUT = (
    "segment_type",
    "file_offset",
    "virtual_address",
    "physical_address",
    "file_size",
    "memory_size",
    "flags",
    "alignment",
)
PROGRAM_HEADER_DEFAULTS = {
    "segment_type": PT_LOAD,
    "file_offset": 0x100,
    "virtual_address": 0x20,
    "physical_address": 0xDEAD_0020,
    "file_size": 4,
    "memory_size": 4,
    "flags": 5,
    "alignment": 1,
}


def program_header(**overrides: int) -> dict[str, int]:
    """Build one fixture entry without production parser dependencies."""
    return PROGRAM_HEADER_DEFAULTS | overrides


def build_elf32_image(
    program_headers: Sequence[Mapping[str, int]],
    *,
    byte_order: str = "little",
    header_overrides: Mapping[str, int] | None = None,
    chunks: Sequence[tuple[int, bytes]] = (),
    table_storage_offset: int | None = None,
) -> bytes:
    """Encode an ELF fixture independently with integer-to-byte operations."""
    overrides = dict(header_overrides or {})
    header_values = {
        "object_type": 2,
        "machine": 8,
        "header_version": 1,
        "entry": 0x0010_0000,
        "program_header_offset": ELF32_HEADER_SIZE,
        "section_header_offset": 0,
        "flags": 0x2092_4001,
        "header_size": ELF32_HEADER_SIZE,
        "program_header_entry_size": ELF32_PROGRAM_HEADER_SIZE,
        "program_header_count": len(program_headers),
        "section_header_entry_size": 40,
        "section_header_count": 0,
        "section_name_string_table_index": 0,
    } | overrides

    identification = bytearray(16)
    identification[:7] = b"\x7fELF\x01\x01\x01"
    identification[5] = 1 if byte_order == "little" else 2
    header_body = b"".join(
        header_values[name].to_bytes(width, byte_order) for name, width in HEADER_FIELD_LAYOUT
    )
    table = b"".join(
        b"".join(entry[name].to_bytes(4, byte_order) for name in PROGRAM_HEADER_FIELD_LAYOUT)
        for entry in program_headers
    )

    table_offset = (
        header_values["program_header_offset"]
        if table_storage_offset is None
        else table_storage_offset
    )
    image_size = max(ELF32_HEADER_SIZE, table_offset + len(table))
    for offset, chunk in chunks:
        image_size = max(image_size, offset + len(chunk))
    image = bytearray(image_size)
    image[:ELF32_HEADER_SIZE] = bytes(identification) + header_body
    image[table_offset : table_offset + len(table)] = table
    for offset, chunk in chunks:
        image[offset : offset + len(chunk)] = chunk
    return bytes(image)


@pytest.mark.unit
@pytest.mark.parametrize("byte_order", ("little", "big"))
def test_parse_program_headers_decodes_all_fields(byte_order: str) -> None:
    """Decode every program-header field using the ELF-declared byte order."""
    fields = program_header(
        segment_type=0x7000_0001,
        file_offset=0x1020_3040,
        virtual_address=0x5060_7080,
        physical_address=0x90A0_B0C0,
        file_size=0x0102_0304,
        memory_size=0x1112_1314,
        flags=0xA5A5_5A5A,
        alignment=0x1000,
    )
    parsed = parse_elf32_program_headers(build_elf32_image([fields], byte_order=byte_order))
    assert parsed == (Elf32ProgramHeader(**fields),)


@pytest.mark.unit
@pytest.mark.parametrize("entry_size", (0, 31, 33))
def test_parse_program_headers_rejects_wrong_entry_size(entry_size: int) -> None:
    """Require the fixed 32-byte Elf32_Phdr layout when entries are present."""
    image = build_elf32_image(
        [program_header()],
        header_overrides={"program_header_entry_size": entry_size},
    )
    with pytest.raises(ElfFormatError, match="entry size"):
        parse_elf32_program_headers(image)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("program_header_offset", "program_header_count"),
    ((ELF32_HEADER_SIZE, 2), (0xFFFF_FFF0, 1)),
)
def test_parse_program_headers_rejects_invalid_table_range(
    program_header_offset: int,
    program_header_count: int,
) -> None:
    """Reject truncated and ELF32-overflowing declared program-header tables."""
    image = build_elf32_image(
        [program_header()],
        header_overrides={
            "program_header_offset": program_header_offset,
            "program_header_count": program_header_count,
        },
        table_storage_offset=ELF32_HEADER_SIZE,
    )
    with pytest.raises(ElfFormatError, match="program-header table"):
        parse_elf32_program_headers(image)


@pytest.mark.unit
def test_load_file_segments_accepts_absent_program_header_table() -> None:
    """Treat an explicitly empty table as an atomic no-op without inventing entries."""
    image = build_elf32_image(
        [],
        header_overrides={
            "program_header_offset": 0,
            "program_header_entry_size": 0,
        },
    )
    memory = bytearray(b"unchanged")
    assert load_ee_elf32_file_segments(memory, image) == ()
    assert memory == b"unchanged"


@pytest.mark.unit
def test_load_file_segments_uses_virtual_addresses_and_preserves_bss() -> None:
    """Load multiple PT_LOAD entries at p_vaddr while leaving M032 zero-fill undone."""
    entries = [
        program_header(file_offset=0x100, virtual_address=0x20, memory_size=8),
        program_header(
            segment_type=4,
            file_offset=0xFFFF_FFF0,
            virtual_address=0xFFFF_FFF0,
            file_size=0xFFFF_FFFF,
            memory_size=0,
            alignment=3,
        ),
        program_header(
            file_offset=0x110,
            virtual_address=0x50,
            physical_address=0x10,
            file_size=3,
            memory_size=6,
            flags=6,
        ),
    ]
    image = build_elf32_image(
        entries,
        chunks=((0x100, b"TEXT"), (0x110, b"DAT")),
    )
    memory = bytearray([0xA5] * 0x80)

    loads = load_ee_elf32_file_segments(memory, image)

    assert [load.program_header_index for load in loads] == [0, 2]
    assert [load.start_address for load in loads] == [0x20, 0x50]
    assert [load.file_size_bytes for load in loads] == [4, 3]
    assert [load.memory_size_bytes for load in loads] == [8, 6]
    assert memory[0x20:0x24] == b"TEXT"
    assert memory[0x24:0x28] == bytes([0xA5] * 4)
    assert memory[0x50:0x53] == b"DAT"
    assert memory[0x53:0x56] == bytes([0xA5] * 3)
    assert memory[:0x20] == bytes([0xA5] * 0x20)
    assert memory[0x56:] == bytes([0xA5] * (0x80 - 0x56))


@pytest.mark.unit
def test_load_file_segments_accepts_empty_segment_at_both_ends() -> None:
    """Allow a zero-sized range at the exclusive source and destination bounds."""
    base = build_elf32_image([])
    entry = program_header(
        file_offset=len(base) + ELF32_PROGRAM_HEADER_SIZE,
        virtual_address=8,
        physical_address=0,
        file_size=0,
        memory_size=0,
    )
    image = build_elf32_image([entry])
    memory = bytearray(b"boundary")
    assert load_ee_elf32_file_segments(memory, image)[0].memory_end_address == len(memory)
    assert memory == b"boundary"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("file_offset", "file_size"),
    ((0x100, 4), (ELF32_ADDRESS_SPACE_SIZE - 2, 4)),
)
def test_load_file_segments_rejects_invalid_source_range_atomically(
    file_offset: int,
    file_size: int,
) -> None:
    """Reject an EOF-crossing or ELF32-overflowing source without mutation."""
    image = build_elf32_image(
        [program_header(file_offset=file_offset, file_size=file_size, memory_size=file_size)]
    )
    memory = bytearray([0xA5] * 0x80)
    before = memory[:]
    with pytest.raises(ElfFormatError, match="file range"):
        load_ee_elf32_file_segments(memory, image)
    assert memory == before


@pytest.mark.unit
@pytest.mark.parametrize(
    ("virtual_address", "memory_size"),
    ((0x7F, 2), (ELF32_ADDRESS_SPACE_SIZE - 2, 4)),
)
def test_load_file_segments_rejects_invalid_destination_range_atomically(
    virtual_address: int,
    memory_size: int,
) -> None:
    """Reject a RAM-crossing or ELF32-overflowing destination without mutation."""
    image = build_elf32_image(
        [
            program_header(
                file_offset=ELF32_HEADER_SIZE + ELF32_PROGRAM_HEADER_SIZE,
                virtual_address=virtual_address,
                file_size=0,
                memory_size=memory_size,
            )
        ]
    )
    memory = bytearray([0xA5] * 0x80)
    before = memory[:]
    with pytest.raises(ElfFormatError, match="range"):
        load_ee_elf32_file_segments(memory, image)
    assert memory == before


@pytest.mark.unit
def test_load_file_segments_rejects_invalid_later_segment_before_any_copy() -> None:
    """Plan the entire image before copying an earlier valid segment."""
    image = build_elf32_image(
        [
            program_header(file_offset=0x100, virtual_address=0x20),
            program_header(file_offset=0x110, virtual_address=0x7F, memory_size=4),
        ],
        chunks=((0x100, b"GOOD"), (0x110, b"LATE")),
    )
    memory = bytearray([0xA5] * 0x80)
    before = memory[:]
    with pytest.raises(ElfFormatError, match="destination size"):
        load_ee_elf32_file_segments(memory, image)
    assert memory == before


@pytest.mark.unit
def test_load_file_segments_rejects_file_size_larger_than_memory_size() -> None:
    """Enforce the PT_LOAD size relation before copying its payload."""
    image = build_elf32_image(
        [program_header(file_size=4, memory_size=3)],
        chunks=((0x100, b"DATA"),),
    )
    memory = bytearray([0xA5] * 0x80)
    before = memory[:]
    with pytest.raises(ElfFormatError, match=r"file size.*exceeds memory size"):
        load_ee_elf32_file_segments(memory, image)
    assert memory == before


@pytest.mark.unit
@pytest.mark.parametrize(
    ("file_offset", "virtual_address", "alignment", "message"),
    ((0x100, 0x20, 3, "power of two"), (0x101, 0x20, 0x10, "congruent")),
)
def test_load_file_segments_rejects_invalid_alignment(
    file_offset: int,
    virtual_address: int,
    alignment: int,
    message: str,
) -> None:
    """Enforce the ABI power-of-two and address-congruence requirements."""
    image = build_elf32_image(
        [
            program_header(
                file_offset=file_offset,
                virtual_address=virtual_address,
                file_size=0,
                memory_size=0,
                alignment=alignment,
            )
        ]
    )
    memory = bytearray([0xA5] * 0x80)
    with pytest.raises(ElfFormatError, match=message):
        load_ee_elf32_file_segments(memory, image)


@pytest.mark.unit
def test_load_file_segments_rejects_out_of_order_load_entries() -> None:
    """Enforce ascending PT_LOAD virtual addresses from the generic ABI."""
    image = build_elf32_image(
        [
            program_header(file_offset=0x100, virtual_address=0x40),
            program_header(file_offset=0x110, virtual_address=0x20),
        ],
        chunks=((0x100, b"HIGH"), (0x110, b"LOW!")),
    )
    memory = bytearray([0xA5] * 0x80)
    before = memory[:]
    with pytest.raises(ElfFormatError, match="ordered"):
        load_ee_elf32_file_segments(memory, image)
    assert memory == before


@pytest.mark.unit
def test_load_file_segments_rejects_overlapping_memory_ranges() -> None:
    """Reject order-dependent overlap, including a future zero-fill region."""
    image = build_elf32_image(
        [
            program_header(file_offset=0x100, virtual_address=0x20, memory_size=0x10),
            program_header(file_offset=0x110, virtual_address=0x28),
        ],
        chunks=((0x100, b"LEFT"), (0x110, b"RITE")),
    )
    memory = bytearray([0xA5] * 0x80)
    before = memory[:]
    with pytest.raises(ElfFormatError, match="overlaps"):
        load_ee_elf32_file_segments(memory, image)
    assert memory == before


@pytest.mark.unit
def test_load_file_segments_requires_mutable_byte_memory() -> None:
    """Reject immutable or unrelated destination objects at the API boundary."""
    image = build_elf32_image([])
    with pytest.raises(TypeError, match="bytearray"):
        load_ee_elf32_file_segments(b"memory", image)  # type: ignore[arg-type]
