"""Directed tests for the independent byte-memory reference model."""

import pytest

from reference.common.byte_memory import ByteMemoryModel

EXPECTED_WORD = 0x6745_2301
EXPECTED_DOUBLEWORD = 0xEFCD_AB89_6745_2301


@pytest.mark.unit
def test_byte_memory_model_reads_little_endian_word() -> None:
    """Form a word through Python's independent byte conversion semantics."""
    model = ByteMemoryModel(8)
    for address, value in enumerate((0x01, 0x23, 0x45, 0x67)):
        model.write_byte(address, value)
    assert model.read32(0) == EXPECTED_WORD


@pytest.mark.unit
@pytest.mark.parametrize("address", (-4, 2, 8))
def test_byte_memory_model_rejects_invalid_read32(address: int) -> None:
    """Reject negative, unaligned, and out-of-range word addresses."""
    model = ByteMemoryModel(8)
    with pytest.raises(ValueError):
        model.read32(address)


@pytest.mark.unit
def test_byte_memory_model_rejects_invalid_byte_writes() -> None:
    """Validate both the address and byte-value domains."""
    model = ByteMemoryModel(8)
    for address, value in ((-1, 0), (8, 0), (0, -1), (0, 0x100)):
        with pytest.raises(ValueError):
            model.write_byte(address, value)


@pytest.mark.unit
def test_byte_memory_model_writes_little_endian_word() -> None:
    """Decompose a word through Python's independent byte conversion semantics."""
    model = ByteMemoryModel(8)
    model.write32(4, EXPECTED_WORD)
    assert tuple(model.data[4:8]) == (0x01, 0x23, 0x45, 0x67)
    assert model.read32(4) == EXPECTED_WORD


@pytest.mark.unit
@pytest.mark.parametrize("address,value", ((-4, 0), (2, 0), (8, 0), (0, -1), (0, 1 << 32)))
def test_byte_memory_model_rejects_invalid_write32(address: int, value: int) -> None:
    """Reject invalid word addresses and values outside 32 bits."""
    model = ByteMemoryModel(8)
    with pytest.raises(ValueError):
        model.write32(address, value)


@pytest.mark.unit
def test_byte_memory_model_applies_every_write32_strobe() -> None:
    """Preserve disabled byte lanes for all sixteen strobe patterns."""
    baseline = bytes((0x11, 0x22, 0x33, 0x44))
    replacement = bytes((0xA1, 0xB2, 0xC3, 0xD4))
    value = int.from_bytes(replacement, byteorder="little", signed=False)
    for strobe in range(16):
        model = ByteMemoryModel(4)
        model.data[:] = baseline
        model.write32_masked(0, value, strobe)
        expected = bytes(
            replacement[lane] if strobe & (1 << lane) else baseline[lane] for lane in range(4)
        )
        assert model.data == expected


@pytest.mark.unit
def test_byte_memory_model_rejects_upper_write32_strobes() -> None:
    """Keep the 32-bit model strobe domain to exactly four byte lanes."""
    model = ByteMemoryModel(4)
    with pytest.raises(ValueError, match="strobe"):
        model.write32_masked(0, 0, 0x10)


@pytest.mark.unit
def test_byte_memory_model_reads_little_endian_doubleword() -> None:
    """Form a doubleword through Python's byte conversion semantics."""
    model = ByteMemoryModel(16)
    for address, value in enumerate((0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF), start=8):
        model.write_byte(address, value)
    assert model.read64(8) == EXPECTED_DOUBLEWORD


@pytest.mark.unit
@pytest.mark.parametrize("address", (-8, 4, 16))
def test_byte_memory_model_rejects_invalid_read64(address: int) -> None:
    """Reject negative, unaligned, and out-of-range doubleword addresses."""
    model = ByteMemoryModel(16)
    with pytest.raises(ValueError):
        model.read64(address)
