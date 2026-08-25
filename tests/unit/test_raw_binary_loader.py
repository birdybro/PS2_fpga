"""Directed tests for the simulation-only raw binary loader."""

from pathlib import Path

import pytest

from sim.loaders.raw_binary import RawBinaryLoad, load_raw_binary, load_raw_binary_file

MEMORY_SIZE = 16
BASELINE = bytes(range(0x40, 0x40 + MEMORY_SIZE))


@pytest.mark.unit
@pytest.mark.parametrize(
    "load_address,payload",
    (
        (0, b"\x01\x23\x45\x67"),
        (5, bytearray((0x89, 0xAB, 0xCD))),
        (MEMORY_SIZE - 2, memoryview(b"\xef\x10")),
    ),
)
def test_load_raw_binary_copies_exact_bytes_and_preserves_neighbors(
    load_address: int,
    payload: bytes | bytearray | memoryview,
) -> None:
    """Copy bytes at first, interior, and final legal destinations."""
    memory = bytearray(BASELINE)
    expected = bytearray(BASELINE)
    expected[load_address : load_address + len(payload)] = payload

    result = load_raw_binary(memory, payload, load_address)

    assert memory == expected
    assert result == RawBinaryLoad(load_address, len(payload))
    assert result.end_address == load_address + len(payload)


@pytest.mark.unit
def test_load_raw_binary_accepts_empty_image_at_memory_end() -> None:
    """Treat an empty range at the exclusive upper bound as a valid no-op."""
    memory = bytearray(BASELINE)
    result = load_raw_binary(memory, b"", MEMORY_SIZE)
    assert memory == BASELINE
    assert result == RawBinaryLoad(MEMORY_SIZE, 0)
    assert result.end_address == MEMORY_SIZE


@pytest.mark.unit
@pytest.mark.parametrize(
    "load_address,payload",
    ((-1, b"\x01"), (MEMORY_SIZE + 1, b""), (MEMORY_SIZE - 1, b"\x01\x02")),
)
def test_load_raw_binary_rejects_invalid_range_without_partial_mutation(
    load_address: int,
    payload: bytes,
) -> None:
    """Validate the whole half-open range before changing any destination byte."""
    memory = bytearray(BASELINE)
    with pytest.raises(ValueError, match="raw binary"):
        load_raw_binary(memory, payload, load_address)
    assert memory == BASELINE


@pytest.mark.unit
@pytest.mark.parametrize(
    "memory,payload,load_address",
    (
        (bytes(MEMORY_SIZE), b"\x01", 0),
        (bytearray(MEMORY_SIZE), [0x01], 0),
        (bytearray(MEMORY_SIZE), b"\x01", True),
        (bytearray(MEMORY_SIZE), b"\x01", "0"),
    ),
)
def test_load_raw_binary_rejects_invalid_argument_types(
    memory: object,
    payload: object,
    load_address: object,
) -> None:
    """Require a mutable byte image, bytes-like input, and integer address."""
    with pytest.raises(TypeError, match="raw binary"):
        load_raw_binary(memory, payload, load_address)  # type: ignore[arg-type]


@pytest.mark.unit
def test_load_raw_binary_file_reads_explicit_external_path(tmp_path: Path) -> None:
    """Read a caller-created file and report its exact populated range."""
    payload = b"\xde\xad\xbe\xef\x55"
    image_path = tmp_path / "fixture.bin"
    image_path.write_bytes(payload)
    memory = bytearray(BASELINE)

    result = load_raw_binary_file(memory, image_path, 3)

    assert memory[:3] == BASELINE[:3]
    assert memory[3:8] == payload
    assert memory[8:] == BASELINE[8:]
    assert result == RawBinaryLoad(3, len(payload))


@pytest.mark.unit
def test_load_raw_binary_file_rejects_oversize_before_mutation(tmp_path: Path) -> None:
    """Reject a file whose complete range cannot fit and preserve memory."""
    image_path = tmp_path / "oversize.bin"
    image_path.write_bytes(bytes(range(MEMORY_SIZE)))
    memory = bytearray(BASELINE)
    with pytest.raises(ValueError, match="exceeds"):
        load_raw_binary_file(memory, image_path, 1)
    assert memory == BASELINE


@pytest.mark.unit
def test_load_raw_binary_file_reports_missing_path(tmp_path: Path) -> None:
    """Propagate the standard missing-file error for an explicit absent path."""
    memory = bytearray(BASELINE)
    with pytest.raises(FileNotFoundError):
        load_raw_binary_file(memory, tmp_path / "missing.bin", 0)
    assert memory == BASELINE
