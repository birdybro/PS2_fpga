"""Directed architectural tests for R5900 LUI."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
SCALAR_MASK = (1 << 64) - 1
OPERATION_LUI = 8


def encode_lui(destination: int, immediate: int) -> int:
    return (0x0F << 26) | (destination << 16) | immediate


def expected_lui(old_destination: int, immediate: int) -> int:
    word = immediate << 16
    scalar = word | ((SCALAR_MASK ^ 0xFFFF_FFFF) if word & (1 << 31) else 0)
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


async def execute_lui(dut, destination: int, immediate: int, old_destination: int) -> int:
    instruction = encode_lui(destination, immediate)
    expected = expected_lui(old_destination, immediate)
    old_pc = int(dut.pc_o.value)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_LUI
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
    assert int(dut.pc_o.value) == (old_pc + 4) & 0xFFFF_FFFF
    await edge(dut)
    return expected


@cocotb.test()
async def test_r5900_lui_boundaries_and_destination_merge(dut) -> None:
    await initialize(dut, 0x1000)
    upper = 0x0123_4567_89AB_CDEF << 64
    cases = (
        (0x0000, 0x0000_0000_0000_0000),
        (0x0001, 0x0000_0000_0001_0000),
        (0x7FFF, 0x0000_0000_7FFF_0000),
        (0x8000, 0xFFFF_FFFF_8000_0000),
        (0xFFFF, 0xFFFF_FFFF_FFFF_0000),
    )
    for immediate, scalar in cases:
        old_destination = upper | 0xAAAA_BBBB_CCCC_DDDD
        await seed_gpr(dut, 5, old_destination)
        assert await execute_lui(dut, 5, immediate, old_destination) == upper | scalar


@cocotb.test()
async def test_r5900_lui_to_zero_retires_and_wraps_pc(dut) -> None:
    await initialize(dut, 0xFFFF_FFFC)
    await execute_lui(dut, 0, 0xFFFF, 0)
    assert int(dut.pc_o.value) == 0


@cocotb.test()
async def test_r5900_lui_rejects_reserved_rs(dut) -> None:
    await initialize(dut, 0x2000)
    illegal = encode_lui(3, 0x1234) | (1 << 21)
    dut.instruction_i.value = illegal
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 0
    assert int(dut.execute_writeback_commit_o.value) == 0
    assert int(dut.reserved_valid_o.value) == 1
    assert int(dut.reserved_instruction_o.value) == illegal
