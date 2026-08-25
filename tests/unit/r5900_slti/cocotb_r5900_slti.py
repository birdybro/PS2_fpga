"""Directed architectural tests for R5900 SLTI."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
SCALAR_WIDTH = 64
SCALAR_MASK = (1 << SCALAR_WIDTH) - 1
WORD_MASK = (1 << 32) - 1
OPERATION_SLTI = 21


def encode_slti(destination: int, source: int, immediate: int) -> int:
    return (0x0A << 26) | (source << 21) | (destination << 16) | immediate


def signed_scalar(value: int) -> int:
    scalar = value & SCALAR_MASK
    return scalar - (1 << SCALAR_WIDTH) if scalar & (1 << (SCALAR_WIDTH - 1)) else scalar


def expected_slti(old_destination: int, source_value: int, immediate: int) -> int:
    signed_immediate = immediate - (1 << 16) if immediate & 0x8000 else immediate
    result = int(signed_scalar(source_value) < signed_immediate)
    return (old_destination & (GPR_MASK ^ SCALAR_MASK)) | result


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


async def execute_slti(
    dut,
    destination: int,
    source: int,
    immediate: int,
    operands: tuple[int, int],
) -> int:
    old_destination, source_value = operands
    instruction = encode_slti(destination, source, immediate)
    expected = expected_slti(old_destination, source_value, immediate)
    old_pc = int(dut.pc_o.value)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_SLTI
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
async def test_r5900_slti_signed_scalar_and_immediate_boundaries(dut) -> None:
    await initialize(dut, 0x1000)
    destination_upper = 0x0123_4567_89AB_CDEF << 64
    cases = (
        (0x0000_0000_0000_0000, 0x0001, 1),
        (0x0000_0000_0000_0001, 0x0000, 0),
        (0xFFFF_FFFF_FFFF_FFFF, 0x0000, 1),
        (0x0000_0000_0000_0000, 0xFFFF, 0),
        (0x8000_0000_0000_0000, 0x0000, 1),
        (0x7FFF_FFFF_FFFF_FFFF, 0xFFFF, 0),
        (0xFFFF_FFFF_FFFF_7FFF, 0x8000, 1),
        (0xFFFF_FFFF_FFFF_8000, 0x8000, 0),
        (0xFFFF_FFFF_7FFF_FFFF, 0x0000, 1),
    )
    for source_scalar, immediate, expected_scalar in cases:
        source_value = 0xFFFF_FFFF_FFFF_FFFF_0000_0000_0000_0000 | source_scalar
        old_destination = destination_upper | 0xAAAA_BBBB_CCCC_DDDD
        await seed_gpr(dut, 4, source_value)
        await seed_gpr(dut, 5, old_destination)
        assert (
            await execute_slti(dut, 5, 4, immediate, (old_destination, source_value))
            == destination_upper | expected_scalar
        )


@cocotb.test()
async def test_r5900_slti_source_destination_alias_and_zero_source(dut) -> None:
    await initialize(dut, 0x2000)
    aliased = 0xCAFE_BABE_1234_5678_FFFF_FFFF_FFFF_FFFF
    await seed_gpr(dut, 31, aliased)
    await execute_slti(dut, 31, 31, 0, (aliased, aliased))
    zero_source_destination = 0x1111_2222_3333_4444_AAAA_BBBB_CCCC_DDDD
    await seed_gpr(dut, 7, zero_source_destination)
    await execute_slti(dut, 7, 0, 1, (zero_source_destination, 0))


@cocotb.test()
async def test_r5900_slti_to_zero_retires_without_writeback_and_wraps_pc(dut) -> None:
    await initialize(dut, 0xFFFF_FFFC)
    source_value = 0x9999_AAAA_BBBB_CCCC_FFFF_FFFF_FFFF_FFFF
    await seed_gpr(dut, 9, source_value)
    await execute_slti(dut, 0, 9, 0, (0, source_value))
    assert int(dut.pc_o.value) == 0
