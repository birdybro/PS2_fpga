"""Clarity-first byte-addressed memory reference model."""

WORD_BYTES = 4
DOUBLEWORD_BYTES = 8
BYTE_WIDTH = 8
MAX_BYTE_VALUE = (1 << BYTE_WIDTH) - 1
MAX_WORD_VALUE = (1 << (WORD_BYTES * BYTE_WIDTH)) - 1
MAX_WORD_STROBE = (1 << WORD_BYTES) - 1
MAX_DOUBLEWORD_VALUE = (1 << (DOUBLEWORD_BYTES * BYTE_WIDTH)) - 1
MAX_DOUBLEWORD_STROBE = (1 << DOUBLEWORD_BYTES) - 1


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

    def read64(self, address: int) -> int:
        """Read one aligned little-endian 64-bit doubleword."""
        if address % DOUBLEWORD_BYTES != 0:
            msg = f"unaligned 64-bit address: {address}"
            raise ValueError(msg)
        end = address + DOUBLEWORD_BYTES
        if address < 0 or end > len(self.data):
            msg = f"64-bit address out of range: {address}"
            raise ValueError(msg)
        return int.from_bytes(self.data[address:end], byteorder="little", signed=False)

    def write32(self, address: int, value: int) -> None:
        """Write one aligned little-endian 32-bit word."""
        self.write32_masked(address, value, MAX_WORD_STROBE)

    def write32_masked(self, address: int, value: int, strobe: int) -> None:
        """Update enabled byte lanes of one aligned little-endian word."""
        if address % WORD_BYTES != 0:
            msg = f"unaligned 32-bit address: {address}"
            raise ValueError(msg)
        end = address + WORD_BYTES
        if address < 0 or end > len(self.data):
            msg = f"32-bit address out of range: {address}"
            raise ValueError(msg)
        if not 0 <= value <= MAX_WORD_VALUE:
            msg = f"32-bit value out of range: {value}"
            raise ValueError(msg)
        if not 0 <= strobe <= MAX_WORD_STROBE:
            msg = f"32-bit byte strobe out of range: {strobe}"
            raise ValueError(msg)
        write_bytes = value.to_bytes(WORD_BYTES, byteorder="little", signed=False)
        for lane, byte_value in enumerate(write_bytes):
            if strobe & (1 << lane):
                self.data[address + lane] = byte_value

    def write64(self, address: int, value: int) -> None:
        """Write one aligned little-endian 64-bit doubleword."""
        self.write64_masked(address, value, MAX_DOUBLEWORD_STROBE)

    def write64_masked(self, address: int, value: int, strobe: int) -> None:
        """Update enabled byte lanes of one aligned little-endian doubleword."""
        if address % DOUBLEWORD_BYTES != 0:
            msg = f"unaligned 64-bit address: {address}"
            raise ValueError(msg)
        end = address + DOUBLEWORD_BYTES
        if address < 0 or end > len(self.data):
            msg = f"64-bit address out of range: {address}"
            raise ValueError(msg)
        if not 0 <= value <= MAX_DOUBLEWORD_VALUE:
            msg = f"64-bit value out of range: {value}"
            raise ValueError(msg)
        if not 0 <= strobe <= MAX_DOUBLEWORD_STROBE:
            msg = f"64-bit byte strobe out of range: {strobe}"
            raise ValueError(msg)
        write_bytes = value.to_bytes(DOUBLEWORD_BYTES, byteorder="little", signed=False)
        for lane, byte_value in enumerate(write_bytes):
            if strobe & (1 << lane):
                self.data[address + lane] = byte_value
