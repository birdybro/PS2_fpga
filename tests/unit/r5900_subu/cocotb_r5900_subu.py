"""Directed architectural tests for R5900 SUBU."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
SCALAR_MASK = (1 << 64) - 1
WORD_MASK = (1 << 32) - 1
OPERATION_NONE = 0
OPERATION_SUBU = 14
RESERVED_TEST_PC = 0x3000


def encode_subu(destination: int, minuend: int, subtrahend: int, shift: int = 0) -> int:
    return (minuend << 21) | (subtrahend << 16) | (destination << 11) | (shift << 6) | 0x23


def expected_subu(old_destination: int, minuend_value: int, subtrahend_value: int) -> int:
    word = ((minuend_value & WORD_MASK) - (subtrahend_value & WORD_MASK)) & WORD_MASK
    scalar = word | ((SCALAR_MASK ^ WORD_MASK) if word & (1 << 31) else 0)
    return (old_destination & (GPR_MASK ^ SCALAR_MASK)) | scalar


async def edge(dut) -> None:
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut, start_pc: int) -> None:
    dut.rst_ni.value = 0
    dut.start_pc_i.value = start_pc
    dut.instruction_valid_i.value = 0
    dut.instruction_i.value = 0
    dut.seed_commit_i.value = 0
    dut.seed_destination_i.value = 0
    dut.seed_value_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1


async def seed_gpr(dut, destination: int, value: int) -> None:
    dut.seed_destination_i.value = destination
    dut.seed_value_i.value = value
    dut.seed_commit_i.value = 1
    await edge(dut)
    dut.seed_commit_i.value = 0
    await edge(dut)


async def execute_subu(
    dut,
    destination: int,
    minuend: int,
    subtrahend: int,
    operands: tuple[int, int, int],
) -> int:
    old_destination, minuend_value, subtrahend_value = operands
    instruction = encode_subu(destination, minuend, subtrahend)
    expected = expected_subu(old_destination, minuend_value, subtrahend_value)
    old_pc = int(dut.pc_o.value)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_SUBU
    assert int(dut.execute_complete_o.value) == 1
    assert int(dut.execute_writeback_destination_o.value) == destination
    assert int(dut.execute_writeback_value_o.value) == expected
    assert int(dut.writeback_valid_o.value) == (destination != 0)
    assert int(dut.retirement_pc_o.value) == old_pc
    assert int(dut.retirement_instruction_o.value) == instruction
    await edge(dut)
    dut.instruction_valid_i.value = 0
    await Timer(1, unit="ns")
    actual = (int(dut.gprs_o.value) >> (destination * GPR_WIDTH)) & GPR_MASK
    assert actual == (0 if destination == 0 else expected)
    assert int(dut.pc_o.value) == (old_pc + 4) & WORD_MASK
    await edge(dut)
    return expected


@cocotb.test()
async def test_r5900_subu_borrow_wrap_and_sign_extension_boundaries(dut) -> None:
    await initialize(dut, 0x1000)
    destination_upper = 0x0123_4567_89AB_CDEF << 64
    cases = (
        (0x0000_0000, 0x0000_0000, 0x0000_0000_0000_0000),
        (0x0000_0001, 0x0000_0000, 0x0000_0000_0000_0001),
        (0x7FFF_FFFF, 0x0000_0000, 0x0000_0000_7FFF_FFFF),
        (0x8000_0000, 0x0000_0000, 0xFFFF_FFFF_8000_0000),
        (0xFFFF_FFFF, 0x0000_0000, 0xFFFF_FFFF_FFFF_FFFF),
        (0x8000_0000, 0x0000_0001, 0x0000_0000_7FFF_FFFF),
        (0x7FFF_FFFF, 0xFFFF_FFFF, 0xFFFF_FFFF_8000_0000),
        (0x0000_0000, 0x0000_0001, 0xFFFF_FFFF_FFFF_FFFF),
    )
    for minuend_word, subtrahend_word, expected_scalar in cases:
        minuend_value = 0xFFFF_FFFF_FFFF_FFFF_1234_5678_0000_0000 | minuend_word
        subtrahend_value = 0xAAAA_AAAA_AAAA_AAAA_8765_4321_0000_0000 | subtrahend_word
        old_destination = destination_upper | 0xAAAA_BBBB_CCCC_DDDD
        await seed_gpr(dut, 3, minuend_value)
        await seed_gpr(dut, 4, subtrahend_value)
        await seed_gpr(dut, 5, old_destination)
        expected = destination_upper | expected_scalar
        assert (
            await execute_subu(
                dut,
                5,
                3,
                4,
                (old_destination, minuend_value, subtrahend_value),
            )
            == expected
        )


@cocotb.test()
async def test_r5900_subu_preserves_operand_order_across_aliases(dut) -> None:
    await initialize(dut, 0x2000)
    minuend = 0xCAFE_BABE_1234_5678_AAAA_BBBB_7FFF_FFFF
    subtrahend = 0x0123_4567_89AB_CDEF_1111_2222_0000_0001
    await seed_gpr(dut, 31, minuend)
    await seed_gpr(dut, 30, subtrahend)
    await execute_subu(dut, 31, 31, 30, (minuend, minuend, subtrahend))
    await seed_gpr(dut, 31, minuend)
    await seed_gpr(dut, 30, subtrahend)
    await execute_subu(dut, 30, 31, 30, (subtrahend, minuend, subtrahend))
    old_destination = 0x9999_AAAA_BBBB_CCCC_DDDD_EEEE_FFFF_0000
    await seed_gpr(dut, 29, old_destination)
    await seed_gpr(dut, 28, subtrahend)
    await execute_subu(dut, 29, 28, 28, (old_destination, subtrahend, subtrahend))


@cocotb.test()
async def test_r5900_subu_to_zero_retires_without_writeback_and_wraps_pc(dut) -> None:
    await initialize(dut, 0xFFFF_FFFC)
    minuend = 0x9999_AAAA_BBBB_CCCC_0123_4567_0000_0000
    subtrahend = 0x1111_2222_3333_4444_FEDC_BA98_0000_0001
    await seed_gpr(dut, 8, minuend)
    await seed_gpr(dut, 9, subtrahend)
    await execute_subu(dut, 0, 8, 9, (0, minuend, subtrahend))
    assert int(dut.pc_o.value) == 0


@cocotb.test()
async def test_r5900_subu_rejects_nonzero_reserved_shift_field(dut) -> None:
    await initialize(dut, RESERVED_TEST_PC)
    destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
    await seed_gpr(dut, 5, destination)
    instruction = encode_subu(5, 3, 4, shift=1)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 0
    assert int(dut.operation_o.value) == OPERATION_NONE
    assert int(dut.execute_complete_o.value) == 0
    assert int(dut.reserved_valid_o.value) == 1
    assert int(dut.reserved_pc_o.value) == RESERVED_TEST_PC
    assert int(dut.reserved_instruction_o.value) == instruction
    await edge(dut)
    assert int(dut.pc_o.value) == RESERVED_TEST_PC
    actual = (int(dut.gprs_o.value) >> (5 * GPR_WIDTH)) & GPR_MASK
    assert actual == destination
