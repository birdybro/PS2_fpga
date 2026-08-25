"""Clarity-first byte-addressed memory reference model."""

WORD_BYTES = 4
BYTE_WIDTH = 8
MAX_BYTE_VALUE = (1 << BYTE_WIDTH) - 1


class ByteMemoryModel:
    """Model bounded bytes and little-endian aligned reads."""

    def __init__(self, size_bytes: int) -> None:
        if size_bytes < WORD_BYTES:
            msg = "byte memory must contain at least four bytes"
            raise ValueError(msg)
        self.data = bytearray(size_bytes)

    def write_byte(self, address: int, value: int) -> None:
        """Store one byte at a validated address."""
        if not 0 <= address < len(self.data):
            msg = f"byte address out of range: {address}"
            raise ValueError(msg)
        if not 0 <= value <= MAX_BYTE_VALUE:
            msg = f"byte value out of range: {value}"
            raise ValueError(msg)
        self.data[address] = value

    def read32(self, address: int) -> int:
        """Read one aligned little-endian 32-bit word."""
        if address % WORD_BYTES != 0:
            msg = f"unaligned 32-bit address: {address}"
            raise ValueError(msg)
        end = address + WORD_BYTES
        if address < 0 or end > len(self.data):
            msg = f"32-bit address out of range: {address}"
            raise ValueError(msg)
        return int.from_bytes(self.data[address:end], byteorder="little", signed=False)
