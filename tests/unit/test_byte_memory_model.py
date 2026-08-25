"""Directed tests for the independent byte-memory reference model."""

import pytest

from reference.common.byte_memory import ByteMemoryModel

EXPECTED_WORD = 0x6745_2301


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
