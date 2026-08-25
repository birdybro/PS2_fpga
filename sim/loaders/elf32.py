"""Generic ELF32 identification and fixed-header parsing."""

import struct
from dataclasses import dataclass
from typing import Literal

ELF_MAGIC = b"\x7fELF"
ELF_IDENT_SIZE = 16
ELF32_HEADER_SIZE = 52
ELFCLASS32 = 1
ELFDATA2LSB = 1
ELFDATA2MSB = 2
EV_CURRENT = 1
ELF32_HEADER_FIELDS = "HHIIIIIHHHHHH"


class ElfFormatError(ValueError):
    """Report a malformed or unsupported generic ELF container field."""


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
    if not isinstance(image, (bytes, bytearray, memoryview)):
        msg = "ELF image must be bytes-like"
        raise TypeError(msg)
    payload = bytes(image)
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
