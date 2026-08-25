"""Generic ELF32 parsing and atomic EE file-backed segment loading."""

import struct
from dataclasses import dataclass
from typing import Literal

ELF_MAGIC = b"\x7fELF"
ELF_IDENT_SIZE = 16
ELF32_HEADER_SIZE = 52
ELF32_PROGRAM_HEADER_SIZE = 32
ELF32_ADDRESS_SPACE_SIZE = 1 << 32
ELFCLASS32 = 1
ELFDATA2LSB = 1
ELFDATA2MSB = 2
EV_CURRENT = 1
ET_EXEC = 2
EM_MIPS = 8
PT_LOAD = 1
ELF32_HEADER_FIELDS = "HHIIIIIHHHHHH"
ELF32_PROGRAM_HEADER_FIELDS = "IIIIIIII"


class ElfFormatError(ValueError):
    """Report a malformed or unsupported generic ELF container field."""


class ElfTargetError(ElfFormatError):
    """Report a well-formed ELF32 header that is not an accepted EE executable."""


@dataclass(frozen=True, slots=True)
class Elf32Header:
    """Decoded generic ELF32 header without target-specific acceptance policy."""

    byte_order: Literal["little", "big"]
    os_abi: int
    abi_version: int
    object_type: int
    machine: int
    header_version: int
    entry: int
    program_header_offset: int
    section_header_offset: int
    flags: int
    header_size: int
    program_header_entry_size: int
    program_header_count: int
    section_header_entry_size: int
    section_header_count: int
    section_name_string_table_index: int


@dataclass(frozen=True, slots=True)
class Elf32ProgramHeader:
    """Decoded fixed-width ELF32 program-header table entry."""

    segment_type: int
    file_offset: int
    virtual_address: int
    physical_address: int
    file_size: int
    memory_size: int
    flags: int
    alignment: int


@dataclass(frozen=True, slots=True)
class Elf32SegmentLoad:
    """Describe one validated file-backed PT_LOAD destination."""

    program_header_index: int
    file_offset: int
    start_address: int
    file_size_bytes: int
    memory_size_bytes: int

    @property
    def file_end_offset(self) -> int:
        """Return the first source byte after the file-backed payload."""
        return self.file_offset + self.file_size_bytes

    @property
    def file_end_address(self) -> int:
        """Return the first destination byte after the file-backed payload."""
        return self.start_address + self.file_size_bytes

    @property
    def memory_end_address(self) -> int:
        """Return the first destination byte after the complete memory segment."""
        return self.start_address + self.memory_size_bytes


def _coerce_elf_image(image: bytes | bytearray | memoryview) -> bytes:
    if not isinstance(image, (bytes, bytearray, memoryview)):
        msg = "ELF image must be bytes-like"
        raise TypeError(msg)
    return bytes(image)


def _parse_identification(payload: bytes) -> tuple[Literal["little", "big"], int, int]:
    if len(payload) < ELF_IDENT_SIZE:
        msg = f"ELF identification is truncated: {len(payload)} bytes"
        raise ElfFormatError(msg)
    if payload[: len(ELF_MAGIC)] != ELF_MAGIC:
        raise ElfFormatError("ELF magic is invalid")
    if payload[4] != ELFCLASS32:
        msg = f"ELF class is not ELF32: {payload[4]}"
        raise ElfFormatError(msg)
    data_encoding = payload[5]
    if data_encoding == ELFDATA2LSB:
        byte_order: Literal["little", "big"] = "little"
    elif data_encoding == ELFDATA2MSB:
        byte_order = "big"
    else:
        msg = f"ELF data encoding is invalid: {data_encoding}"
        raise ElfFormatError(msg)
    if payload[6] != EV_CURRENT:
        msg = f"ELF identification version is invalid: {payload[6]}"
        raise ElfFormatError(msg)
    return byte_order, payload[7], payload[8]


def parse_elf32_header(image: bytes | bytearray | memoryview) -> Elf32Header:
    """Parse a complete generic ELF32 header without applying EE target policy."""
    payload = _coerce_elf_image(image)
    byte_order, os_abi, abi_version = _parse_identification(payload)
    if len(payload) < ELF32_HEADER_SIZE:
        msg = f"ELF32 header is truncated: {len(payload)} of {ELF32_HEADER_SIZE} bytes"
        raise ElfFormatError(msg)

    prefix = "<" if byte_order == "little" else ">"
    fields = struct.unpack_from(prefix + ELF32_HEADER_FIELDS, payload, ELF_IDENT_SIZE)
    header = Elf32Header(byte_order, os_abi, abi_version, *fields)
    if header.header_version != EV_CURRENT:
        msg = f"ELF header version is invalid: {header.header_version}"
        raise ElfFormatError(msg)
    if header.header_size != ELF32_HEADER_SIZE:
        msg = f"ELF32 header size is invalid: {header.header_size}"
        raise ElfFormatError(msg)
    return header


def _parse_program_headers(
    payload: bytes,
    header: Elf32Header,
) -> tuple[Elf32ProgramHeader, ...]:
    if header.program_header_count == 0:
        return ()
    if header.program_header_entry_size != ELF32_PROGRAM_HEADER_SIZE:
        msg = f"ELF32 program-header entry size is invalid: {header.program_header_entry_size}"
        raise ElfFormatError(msg)

    table_start = header.program_header_offset
    table_size = header.program_header_count * ELF32_PROGRAM_HEADER_SIZE
    table_end = table_start + table_size
    if table_end > ELF32_ADDRESS_SPACE_SIZE:
        msg = f"ELF32 program-header table range overflows: [{table_start}, {table_end})"
        raise ElfFormatError(msg)
    if table_start > len(payload) or table_end > len(payload):
        msg = (
            f"ELF32 program-header table [{table_start}, {table_end}) exceeds "
            f"image size {len(payload)}"
        )
        raise ElfFormatError(msg)

    prefix = "<" if header.byte_order == "little" else ">"
    return tuple(
        Elf32ProgramHeader(
            *struct.unpack_from(
                prefix + ELF32_PROGRAM_HEADER_FIELDS,
                payload,
                table_start + index * ELF32_PROGRAM_HEADER_SIZE,
            )
        )
        for index in range(header.program_header_count)
    )


def parse_elf32_program_headers(
    image: bytes | bytearray | memoryview,
) -> tuple[Elf32ProgramHeader, ...]:
    """Parse the generic ELF32 program-header table in declared byte order."""
    payload = _coerce_elf_image(image)
    return _parse_program_headers(payload, parse_elf32_header(payload))


def validate_ee_elf32_header(header: Elf32Header) -> Elf32Header:
    """Accept the documented native EE executable target without mutating state."""
    if not isinstance(header, Elf32Header):
        msg = "EE target validation requires an Elf32Header"
        raise TypeError(msg)
    if header.object_type != ET_EXEC:
        msg = f"EE ELF object type is not ET_EXEC: {header.object_type}"
        raise ElfTargetError(msg)
    if header.machine != EM_MIPS:
        msg = f"EE ELF machine is not EM_MIPS: {header.machine}"
        raise ElfTargetError(msg)
    if header.byte_order != "little":
        msg = f"EE ELF data encoding is not little-endian: {header.byte_order}"
        raise ElfTargetError(msg)
    return header


def parse_ee_elf32_header(image: bytes | bytearray | memoryview) -> Elf32Header:
    """Parse generic ELF32 fields and apply the native EE target policy."""
    return validate_ee_elf32_header(parse_elf32_header(image))


def _validate_elf_memory(memory: bytearray) -> None:
    if not isinstance(memory, bytearray):
        msg = "EE ELF destination must be a bytearray"
        raise TypeError(msg)


def _is_power_of_two(value: int) -> bool:
    return value > 0 and (value & (value - 1)) == 0


def _validate_file_segment_load(
    index: int,
    program_header: Elf32ProgramHeader,
    memory_size: int,
    image_size: int,
) -> Elf32SegmentLoad:
    if program_header.file_size > program_header.memory_size:
        msg = (
            f"ELF32 PT_LOAD[{index}] file size {program_header.file_size} "
            f"exceeds memory size {program_header.memory_size}"
        )
        raise ElfFormatError(msg)
    if program_header.alignment not in (0, 1):
        if not _is_power_of_two(program_header.alignment):
            msg = (
                f"ELF32 PT_LOAD[{index}] alignment is not a power of two: "
                f"{program_header.alignment}"
            )
            raise ElfFormatError(msg)
        if (
            program_header.virtual_address % program_header.alignment
            != program_header.file_offset % program_header.alignment
        ):
            msg = f"ELF32 PT_LOAD[{index}] file and virtual addresses are not congruent"
            raise ElfFormatError(msg)

    file_end = program_header.file_offset + program_header.file_size
    memory_end = program_header.virtual_address + program_header.memory_size
    if file_end > ELF32_ADDRESS_SPACE_SIZE:
        msg = f"ELF32 PT_LOAD[{index}] file range overflows"
        raise ElfFormatError(msg)
    if memory_end > ELF32_ADDRESS_SPACE_SIZE:
        msg = f"ELF32 PT_LOAD[{index}] virtual-address range overflows"
        raise ElfFormatError(msg)
    if program_header.file_offset > image_size or file_end > image_size:
        msg = (
            f"ELF32 PT_LOAD[{index}] file range "
            f"[{program_header.file_offset}, {file_end}) exceeds image size {image_size}"
        )
        raise ElfFormatError(msg)
    if program_header.virtual_address > memory_size or memory_end > memory_size:
        msg = (
            f"ELF32 PT_LOAD[{index}] memory range "
            f"[{program_header.virtual_address}, {memory_end}) exceeds "
            f"destination size {memory_size}"
        )
        raise ElfFormatError(msg)
    return Elf32SegmentLoad(
        program_header_index=index,
        file_offset=program_header.file_offset,
        start_address=program_header.virtual_address,
        file_size_bytes=program_header.file_size,
        memory_size_bytes=program_header.memory_size,
    )


def _plan_file_segment_loads(
    memory_size: int,
    image_size: int,
    program_headers: tuple[Elf32ProgramHeader, ...],
) -> tuple[Elf32SegmentLoad, ...]:
    loads: list[Elf32SegmentLoad] = []
    previous_virtual_address: int | None = None

    for index, program_header in enumerate(program_headers):
        if program_header.segment_type != PT_LOAD:
            continue
        if (
            previous_virtual_address is not None
            and program_header.virtual_address < previous_virtual_address
        ):
            msg = "ELF32 PT_LOAD entries are not ordered by virtual address"
            raise ElfFormatError(msg)
        previous_virtual_address = program_header.virtual_address
        load = _validate_file_segment_load(index, program_header, memory_size, image_size)
        for existing in loads:
            if (
                load.start_address < existing.memory_end_address
                and existing.start_address < load.memory_end_address
            ):
                msg = (
                    f"ELF32 PT_LOAD[{index}] memory range overlaps "
                    f"PT_LOAD[{existing.program_header_index}]"
                )
                raise ElfFormatError(msg)
        loads.append(load)
    return tuple(loads)


def _prepare_ee_segment_load(
    memory: bytearray,
    image: bytes | bytearray | memoryview,
) -> tuple[bytes, tuple[Elf32SegmentLoad, ...]]:
    _validate_elf_memory(memory)
    payload = _coerce_elf_image(image)
    header = parse_ee_elf32_header(payload)
    program_headers = _parse_program_headers(payload, header)
    loads = _plan_file_segment_loads(len(memory), len(payload), program_headers)
    return payload, loads


def load_ee_elf32_file_segments(
    memory: bytearray,
    image: bytes | bytearray | memoryview,
) -> tuple[Elf32SegmentLoad, ...]:
    """Atomically copy EE PT_LOAD file bytes to their virtual addresses."""
    payload, loads = _prepare_ee_segment_load(memory, image)

    for load in loads:
        memory[load.start_address : load.file_end_address] = payload[
            load.file_offset : load.file_end_offset
        ]
    return loads


def load_ee_elf32_segments(
    memory: bytearray,
    image: bytes | bytearray | memoryview,
) -> tuple[Elf32SegmentLoad, ...]:
    """Atomically load EE PT_LOAD file bytes and zero each memory-only tail."""
    payload, loads = _prepare_ee_segment_load(memory, image)

    for load in loads:
        memory[load.start_address : load.file_end_address] = payload[
            load.file_offset : load.file_end_offset
        ]
        zero_fill_size = load.memory_size_bytes - load.file_size_bytes
        memory[load.file_end_address : load.memory_end_address] = bytes(zero_fill_size)
    return loads
