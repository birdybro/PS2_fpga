"""Directed architectural tests for R5900 signed word DIV."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
SCALAR_MASK = (1 << 64) - 1
WORD_MASK = (1 << 32) - 1
OPERATION_NONE = 0
OPERATION_DIV = 37
HI1_SEED = 0x3333_4444_5555_6666
LO1_SEED = 0x7777_8888_9999_AAAA
RESERVED_TEST_PC = 0x3000


def encode_div(dividend: int, divisor: int, reserved: int = 0) -> int:
    """Encode DIV while allowing explicit reserved-field negative tests."""
    return (dividend << 21) | (divisor << 16) | (reserved << 6) | 0x1A


def signed_word(value: int) -> int:
    """Interpret one low word as a Python signed integer."""
    word = value & WORD_MASK
    return word - (1 << 32) if word & (1 << 31) else word


def expected_div(dividend_value: int, divisor_value: int) -> tuple[int, int]:
    """Calculate independently specified HI remainder and LO quotient."""
    dividend = signed_word(dividend_value)
    divisor = signed_word(divisor_value)
    if dividend == -(1 << 31) and divisor == -1:
        quotient, remainder = dividend, 0
    elif divisor == 0:
        quotient, remainder = (1 if dividend < 0 else -1), dividend
    else:
        magnitude = abs(dividend) // abs(divisor)
        quotient = -magnitude if (dividend < 0) != (divisor < 0) else magnitude
        remainder = dividend - quotient * divisor
    return remainder & SCALAR_MASK, quotient & SCALAR_MASK


async def edge(dut) -> None:
    """Advance one clock and allow combinational state to settle."""
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut, start_pc: int) -> None:
    """Reset the harness and seed both HI/LO accumulator lanes."""
    dut.rst_ni.value = 0
    dut.start_pc_i.value = start_pc
    dut.instruction_valid_i.value = 0
    dut.instruction_i.value = 0
    dut.seed_gpr_commit_i.value = 0
    dut.seed_gpr_destination_i.value = 0
    dut.seed_gpr_value_i.value = 0
    dut.seed_hilo_commit_i.value = 0
    dut.seed_hi_i.value = 0
    dut.seed_lo_i.value = 0
    dut.seed_hi1_i.value = 0
    dut.seed_lo1_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1
    dut.seed_hilo_commit_i.value = 1
    dut.seed_hi_i.value = 0x1111
    dut.seed_lo_i.value = 0x2222
    dut.seed_hi1_i.value = HI1_SEED
    dut.seed_lo1_i.value = LO1_SEED
    await edge(dut)
    dut.seed_hilo_commit_i.value = 0


async def seed_gpr(dut, destination: int, value: int) -> None:
    """Initialize one GPR through the architectural writeback boundary."""
    dut.seed_gpr_destination_i.value = destination
    dut.seed_gpr_value_i.value = value
    dut.seed_gpr_commit_i.value = 1
    await edge(dut)
    dut.seed_gpr_commit_i.value = 0
    await edge(dut)


async def execute_div(
    dut,
    fields: tuple[int, int],
    source_values: tuple[int, int],
) -> tuple[int, int]:
    """Execute one legal DIV and verify all visible combinational events and state."""
    dividend_register, divisor_register = fields
    dividend_value, divisor_value = source_values
    instruction = encode_div(dividend_register, divisor_register)
    expected_hi, expected_lo = expected_div(dividend_value, divisor_value)
    old_pc = int(dut.pc_o.value)
    old_gprs = int(dut.gprs_o.value)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_DIV
    assert int(dut.execute_complete_o.value) == 1
    assert int(dut.pc_advance_o.value) == 1
    assert int(dut.execute_write_hi_valid_o.value) == 1
    assert int(dut.execute_write_hi_value_o.value) == expected_hi
    assert int(dut.execute_write_lo_valid_o.value) == 1
    assert int(dut.execute_write_lo_value_o.value) == expected_lo
    assert int(dut.execute_writeback_commit_o.value) == 0
    assert int(dut.execute_writeback_destination_o.value) == 0
    assert int(dut.execute_writeback_value_o.value) == 0
    assert int(dut.writeback_valid_o.value) == 0
    assert int(dut.retirement_valid_o.value) == 1
    assert int(dut.retirement_pc_o.value) == old_pc
    assert int(dut.retirement_instruction_o.value) == instruction
    assert int(dut.reserved_valid_o.value) == 0
    await edge(dut)
    dut.instruction_valid_i.value = 0
    await Timer(1, unit="ns")
    assert int(dut.gprs_o.value) == old_gprs
    assert (int(dut.hi_o.value), int(dut.lo_o.value)) == (expected_hi, expected_lo)
    assert (int(dut.hi1_o.value), int(dut.lo1_o.value)) == (HI1_SEED, LO1_SEED)
    assert int(dut.pc_o.value) == (old_pc + 4) & WORD_MASK
    await edge(dut)
    return expected_hi, expected_lo


@cocotb.test()
async def test_r5900_div_signed_quotient_remainder_and_low_word_sources(dut) -> None:
    """Cover all sign pairings, truncation toward zero, and ignored upper lanes."""
    await initialize(dut, 0x1000)
    cases = (
        (7, 3, 1, 2),
        (-7, 3, -1, -2),
        (7, -3, 1, -2),
        (-7, -3, -1, 2),
        ((1 << 31) - 1, 1, 0, (1 << 31) - 1),
        (-(1 << 31), 2, 0, -(1 << 30)),
    )
    for dividend_word, divisor_word, expected_hi, expected_lo in cases:
        dividend = 0xDEAD_BEEF_CAFE_F00D_1234_5678_0000_0000 | (dividend_word & WORD_MASK)
        divisor = 0xAAAA_5555_AAAA_5555_8765_4321_0000_0000 | (divisor_word & WORD_MASK)
        await seed_gpr(dut, 3, dividend)
        await seed_gpr(dut, 4, divisor)
        assert await execute_div(dut, (3, 4), (dividend, divisor)) == (
            expected_hi & SCALAR_MASK,
            expected_lo & SCALAR_MASK,
        )


@cocotb.test()
async def test_r5900_div_zero_divisor_has_defined_r5900_results(dut) -> None:
    """Check positive, negative, and zero dividend behavior at divisor zero."""
    await initialize(dut, 0x2000)
    for dividend_word, expected_hi, expected_lo in (
        (7, 7, -1),
        (-7, -7, 1),
        (0, 0, -1),
    ):
        dividend = 0xCAFE_BABE_1234_5678_0000_0000_0000_0000 | (dividend_word & WORD_MASK)
        await seed_gpr(dut, 8, dividend)
        assert await execute_div(dut, (8, 0), (dividend, 0)) == (
            expected_hi & SCALAR_MASK,
            expected_lo & SCALAR_MASK,
        )


@cocotb.test()
async def test_r5900_div_overflow_and_pc_wrap(dut) -> None:
    """Define the sole signed overflow pair and preserve normal retirement."""
    await initialize(dut, 0xFFFF_FFFC)
    dividend = 0xABCD_EF01_2345_6789_8000_0000
    divisor = 0x1111_2222_3333_4444_FFFF_FFFF
    await seed_gpr(dut, 31, dividend)
    await seed_gpr(dut, 30, divisor)
    assert await execute_div(dut, (31, 30), (dividend, divisor)) == (
        0,
        0xFFFF_FFFF_8000_0000,
    )
    assert int(dut.pc_o.value) == 0


@cocotb.test()
async def test_r5900_div_rejects_nonzero_reserved_rd_or_sa(dut) -> None:
    """Reject every class of noncanonical DIV reserved-field population."""
    await initialize(dut, RESERVED_TEST_PC)
    for reserved in (1, 1 << 5, 0x3FF):
        instruction = encode_div(3, 4, reserved=reserved)
        dut.instruction_i.value = instruction
        dut.instruction_valid_i.value = 1
        await Timer(1, unit="ns")
        assert int(dut.execute_valid_o.value) == 0
        assert int(dut.operation_o.value) == OPERATION_NONE
        assert int(dut.execute_complete_o.value) == 0
        assert int(dut.execute_write_hi_valid_o.value) == 0
        assert int(dut.execute_write_lo_valid_o.value) == 0
        assert int(dut.reserved_valid_o.value) == 1
        assert int(dut.reserved_pc_o.value) == RESERVED_TEST_PC
        assert int(dut.reserved_instruction_o.value) == instruction
