"""Directed field-extraction tests for 32-bit R5900 instruction words."""

import cocotb
from cocotb.triggers import Timer

WORD_MASK = (1 << 32) - 1


def expected_fields(word: int) -> dict[str, int]:
    """Extract expected MIPS-format fields with independent integer operations."""
    immediate = word & 0xFFFF
    sign_extended = immediate | 0xFFFF_0000 if immediate & 0x8000 else immediate
    return {
        "opcode_o": (word >> 26) & 0x3F,
        "rs_o": (word >> 21) & 0x1F,
        "rt_o": (word >> 16) & 0x1F,
        "rd_o": (word >> 11) & 0x1F,
        "shift_amount_o": (word >> 6) & 0x1F,
        "function_o": word & 0x3F,
        "immediate_o": immediate,
        "immediate_sign_extended_o": sign_extended,
        "immediate_zero_extended_o": immediate,
        "target_o": word & 0x03FF_FFFF,
    }


async def check_word(dut, word: int) -> None:
    """Drive one word and compare every overlapping format view."""
    dut.instruction_i.value = word
    await Timer(1, unit="ns")
    for signal_name, expected in expected_fields(word).items():
        actual = int(getattr(dut, signal_name).value)
        assert actual == expected, (
            f"word=0x{word:08x} field={signal_name} expected=0x{expected:x} actual=0x{actual:x}"
        )


@cocotb.test()
async def test_r5900_instruction_fields_extract_format_boundaries(dut) -> None:
    """Cover zero, all-one, alternating, and asymmetric complete words."""
    for word in (
        0,
        WORD_MASK,
        0xAAAA_AAAA,
        0x5555_5555,
        0x0123_4567,
        0xFEDC_BA98,
    ):
        await check_word(dut, word)


@cocotb.test()
async def test_r5900_instruction_fields_isolate_each_non_immediate_field(dut) -> None:
    """Place minimum, single-bit, alternating, and maximum values in each field."""
    field_ranges = (
        (26, 6),
        (21, 5),
        (16, 5),
        (11, 5),
        (6, 5),
        (0, 6),
    )
    for shift, width in field_ranges:
        mask = (1 << width) - 1
        for value in (0, 1, mask >> 1, 1 << (width - 1), mask):
            await check_word(dut, value << shift)


@cocotb.test()
async def test_r5900_instruction_fields_extend_immediate_boundaries(dut) -> None:
    """Distinguish zero extension from two's-complement sign extension."""
    for upper_16 in (0, 0x1234, 0xFFFF):
        for immediate in (0, 1, 0x7FFF, 0x8000, 0x8001, 0xAAAA, 0xFFFF):
            await check_word(dut, (upper_16 << 16) | immediate)
