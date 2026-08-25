"""Atomic raw-binary loading into a bounded simulation memory image."""

from dataclasses import dataclass
from os import PathLike
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RawBinaryLoad:
    """Describe the half-open destination range populated by one load."""

    start_address: int
    size_bytes: int

    @property
    def end_address(self) -> int:
        """Return the first destination address after the loaded image."""
        return self.start_address + self.size_bytes


def _validate_memory(memory: bytearray) -> None:
    if not isinstance(memory, bytearray):
        msg = "raw binary destination must be a bytearray"
        raise TypeError(msg)


def _validate_load_range(memory: bytearray, load_address: int, size_bytes: int) -> RawBinaryLoad:
    _validate_memory(memory)
    if not isinstance(load_address, int) or isinstance(load_address, bool):
        msg = "raw binary load address must be an integer"
        raise TypeError(msg)
    if load_address < 0:
        msg = f"raw binary load address is negative: {load_address}"
        raise ValueError(msg)
    end_address = load_address + size_bytes
    if load_address > len(memory) or end_address > len(memory):
        msg = (
            f"raw binary range [{load_address}, {end_address}) exceeds "
            f"destination size {len(memory)}"
        )
        raise ValueError(msg)
    return RawBinaryLoad(start_address=load_address, size_bytes=size_bytes)


def load_raw_binary(
    memory: bytearray,
    image: bytes | bytearray | memoryview,
    load_address: int,
) -> RawBinaryLoad:
    """Copy one bytes-like image after validating its complete destination range."""
    if not isinstance(image, (bytes, bytearray, memoryview)):
        msg = "raw binary image must be bytes-like"
        raise TypeError(msg)
    payload = bytes(image)
    result = _validate_load_range(memory, load_address, len(payload))
    memory[result.start_address : result.end_address] = payload
    return result


def load_raw_binary_file(
    memory: bytearray,
    path: str | PathLike[str],
    load_address: int,
) -> RawBinaryLoad:
    """Load an explicit external file without embedding it in the simulator."""
    _validate_memory(memory)
    path_object = Path(path)
    file_size = path_object.stat().st_size
    _validate_load_range(memory, load_address, file_size)
    return load_raw_binary(memory, path_object.read_bytes(), load_address)
