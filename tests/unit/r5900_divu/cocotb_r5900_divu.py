"""Directed architectural tests for R5900 unsigned word DIVU."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
WORD_MASK = (1 << 32) - 1
SCALAR_MASK = (1 << 64) - 1
OPERATION_NONE = 0
OPERATION_DIVU = 38
HI1_SEED = 0x3333_4444_5555_6666
LO1_SEED = 0x7777_8888_9999_AAAA
RESERVED_TEST_PC = 0x3000


def encode_divu(dividend: int, divisor: int, reserved: int = 0) -> int:
    """Encode DIVU while allowing explicit reserved-field negative tests."""
    return (dividend << 21) | (divisor << 16) | (reserved << 6) | 0x1B


def sign_extend_word(value: int) -> int:
    """Sign-extend a quotient or remainder word into its scalar destination."""
    word = value & WORD_MASK
    return word | ((SCALAR_MASK ^ WORD_MASK) if word & (1 << 31) else 0)


def expected_divu(dividend_value: int, divisor_value: int) -> tuple[int, int]:
    """Calculate independently specified HI remainder and LO quotient."""
    dividend = dividend_value & WORD_MASK
    divisor = divisor_value & WORD_MASK
    if divisor == 0:
        quotient, remainder = WORD_MASK, dividend
    else:
        quotient, remainder = divmod(dividend, divisor)
    return sign_extend_word(remainder), sign_extend_word(quotient)


async def edge(dut) -> None:
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut, start_pc: int) -> None:
    """Reset the harness and explicitly seed all HI/LO-family state."""
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
    dut.seed_gpr_destination_i.value = destination
    dut.seed_gpr_value_i.value = value
    dut.seed_gpr_commit_i.value = 1
    await edge(dut)
    dut.seed_gpr_commit_i.value = 0
    await edge(dut)


async def execute_divu(dut, fields: tuple[int, int], values: tuple[int, int]) -> tuple[int, int]:
    """Execute one DIVU and compare every visible event and state update."""
    dividend_register, divisor_register = fields
    instruction = encode_divu(dividend_register, divisor_register)
    expected_hi, expected_lo = expected_divu(*values)
    old_pc = int(dut.pc_o.value)
    old_gprs = int(dut.gprs_o.value)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_DIVU
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
async def test_r5900_divu_unsigned_extrema_and_result_extension(dut) -> None:
    """Cover unsigned division and independent sign extension of both results."""
    await initialize(dut, 0x1000)
    cases = (
        (0, 1),
        (1, 1),
        (7, 3),
        (0x7FFF_FFFF, 1),
        (0x8000_0000, 1),
        (0xFFFF_FFFF, 1),
        (0xFFFF_FFFF, 0x8000_0000),
        (0xFFFF_FFFF, 2),
    )
    for dividend_word, divisor_word in cases:
        dividend = 0xDEAD_BEEF_CAFE_F00D_1234_5678_0000_0000 | dividend_word
        divisor = 0xAAAA_5555_AAAA_5555_8765_4321_0000_0000 | divisor_word
        await seed_gpr(dut, 3, dividend)
        await seed_gpr(dut, 4, divisor)
        await execute_divu(dut, (3, 4), (dividend, divisor))


@cocotb.test()
async def test_r5900_divu_zero_divisor_retains_dividend_word(dut) -> None:
    """Require all-ones LO and sign-extended dividend in HI for divisor zero."""
    await initialize(dut, 0x2000)
    for dividend_word in (0, 1, 0x7FFF_FFFF, 0x8000_0000, 0xFFFF_FFFF):
        dividend = 0xCAFE_BABE_1234_5678_0000_0000_0000_0000 | dividend_word
        await seed_gpr(dut, 8, dividend)
        assert await execute_divu(dut, (8, 0), (dividend, 0)) == (
            sign_extend_word(dividend_word),
            SCALAR_MASK,
        )


@cocotb.test()
async def test_r5900_divu_source_alias_and_pc_wrap(dut) -> None:
    """Divide one maximum unsigned source by itself and wrap the PC."""
    await initialize(dut, 0xFFFF_FFFC)
    source = 0xABCD_EF01_2345_6789_FFFF_FFFF
    await seed_gpr(dut, 31, source)
    assert await execute_divu(dut, (31, 31), (source, source)) == (0, 1)
    assert int(dut.pc_o.value) == 0


@cocotb.test()
async def test_r5900_divu_rejects_nonzero_reserved_rd_or_sa(dut) -> None:
    """Reject every class of noncanonical DIVU reserved-field population."""
    await initialize(dut, RESERVED_TEST_PC)
    for reserved in (1, 1 << 5, 0x3FF):
        instruction = encode_divu(3, 4, reserved=reserved)
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
