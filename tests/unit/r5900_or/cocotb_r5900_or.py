"""Directed architectural tests for R5900 OR."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
SCALAR_MASK = (1 << 64) - 1
WORD_MASK = (1 << 32) - 1
OPERATION_NONE = 0
OPERATION_OR = 16
RESERVED_TEST_PC = 0x3000


def encode_or(destination: int, source_a: int, source_b: int, shift: int = 0) -> int:
    return (source_a << 21) | (source_b << 16) | (destination << 11) | (shift << 6) | 0x25


def expected_or(old_destination: int, source_a_value: int, source_b_value: int) -> int:
    scalar = (source_a_value | source_b_value) & SCALAR_MASK
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


async def execute_or(
    dut,
    destination: int,
    source_a: int,
    source_b: int,
    operands: tuple[int, int, int],
) -> int:
    old_destination, source_a_value, source_b_value = operands
    instruction = encode_or(destination, source_a, source_b)
    expected = expected_or(old_destination, source_a_value, source_b_value)
    old_pc = int(dut.pc_o.value)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_OR
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
async def test_r5900_or_scalar_patterns_and_lane_boundaries(dut) -> None:
    await initialize(dut, 0x1000)
    destination_upper = 0x0123_4567_89AB_CDEF << 64
    cases = (
        (0x0000_0000_0000_0000, 0x0000_0000_0000_0000, 0x0000_0000_0000_0000),
        (0x0000_0000_0000_0000, 0xFFFF_FFFF_FFFF_FFFF, 0xFFFF_FFFF_FFFF_FFFF),
        (0xAAAA_AAAA_AAAA_AAAA, 0x5555_5555_5555_5555, 0xFFFF_FFFF_FFFF_FFFF),
        (0xFFFF_0000_FFFF_0000, 0x0F0F_0F0F_0F0F_0F0F, 0xFFFF_0F0F_FFFF_0F0F),
        (0x8000_0000_0000_0000, 0x0000_0000_0000_0001, 0x8000_0000_0000_0001),
        (0x0000_0001_0000_0000, 0x0000_0000_0000_0001, 0x0000_0001_0000_0001),
        (0xFFFF_FFFF_0000_0000, 0x0000_0000_FFFF_FFFF, 0xFFFF_FFFF_FFFF_FFFF),
        (0x0123_4567_89AB_CDEF, 0xFF00_FF00_FF00_FF00, 0xFF23_FF67_FFAB_FFEF),
    )
    for source_a_scalar, source_b_scalar, expected_scalar in cases:
        source_a_value = 0xFFFF_FFFF_FFFF_FFFF_0000_0000_0000_0000 | source_a_scalar
        source_b_value = 0xAAAA_AAAA_AAAA_AAAA_0000_0000_0000_0000 | source_b_scalar
        old_destination = destination_upper | 0xAAAA_BBBB_CCCC_DDDD
        await seed_gpr(dut, 3, source_a_value)
        await seed_gpr(dut, 4, source_b_value)
        await seed_gpr(dut, 5, old_destination)
        expected = destination_upper | expected_scalar
        assert (
            await execute_or(
                dut,
                5,
                3,
                4,
                (old_destination, source_a_value, source_b_value),
            )
            == expected
        )


@cocotb.test()
async def test_r5900_or_handles_both_destination_aliases_and_identical_sources(dut) -> None:
    await initialize(dut, 0x2000)
    source_a = 0xCAFE_BABE_1234_5678_F0F0_F0F0_AAAA_5555
    source_b = 0x0123_4567_89AB_CDEF_0FF0_00FF_FFFF_0000
    await seed_gpr(dut, 31, source_a)
    await seed_gpr(dut, 30, source_b)
    await execute_or(dut, 31, 31, 30, (source_a, source_a, source_b))
    await seed_gpr(dut, 31, source_a)
    await seed_gpr(dut, 30, source_b)
    await execute_or(dut, 30, 31, 30, (source_b, source_a, source_b))
    old_destination = 0x9999_AAAA_BBBB_CCCC_DDDD_EEEE_FFFF_0000
    await seed_gpr(dut, 29, old_destination)
    await seed_gpr(dut, 28, source_b)
    await execute_or(dut, 29, 28, 28, (old_destination, source_b, source_b))


@cocotb.test()
async def test_r5900_or_to_zero_retires_without_writeback_and_wraps_pc(dut) -> None:
    await initialize(dut, 0xFFFF_FFFC)
    source_a = 0x9999_AAAA_BBBB_CCCC_F0F0_F0F0_AAAA_5555
    source_b = 0x1111_2222_3333_4444_0FF0_00FF_FFFF_0000
    await seed_gpr(dut, 8, source_a)
    await seed_gpr(dut, 9, source_b)
    await execute_or(dut, 0, 8, 9, (0, source_a, source_b))
    assert int(dut.pc_o.value) == 0


@cocotb.test()
async def test_r5900_or_rejects_nonzero_reserved_shift_field(dut) -> None:
    await initialize(dut, RESERVED_TEST_PC)
    destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
    await seed_gpr(dut, 5, destination)
    instruction = encode_or(5, 3, 4, shift=1)
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
