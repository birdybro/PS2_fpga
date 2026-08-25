"""Directed architectural tests for R5900 DSRL32."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
SCALAR_MASK = (1 << 64) - 1
OPERATION_DSRL32 = 27
ENCODED_DSRL32_EXAMPLE = 0x0011_FB7E
ALIASED_DSRL32_RESULT = 0xCAFE_BABE_1234_5678_0000_0000_0FED_CBA9


def encode(destination: int, source: int, count: int) -> int:
    return (source << 16) | (destination << 11) | (count << 6) | 0x3E


async def edge(dut) -> None:
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut, pc: int) -> None:
    dut.rst_ni.value = 0
    dut.start_pc_i.value = pc
    dut.instruction_valid_i.value = 0
    dut.instruction_i.value = 0
    dut.seed_commit_i.value = 0
    dut.seed_destination_i.value = 0
    dut.seed_value_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1


async def seed_gpr(dut, index: int, value: int) -> None:
    dut.seed_destination_i.value = index
    dut.seed_value_i.value = value
    dut.seed_commit_i.value = 1
    await edge(dut)
    dut.seed_commit_i.value = 0
    await edge(dut)


async def execute(dut, destination: int, source: int, count: int, old_rd: int) -> int:
    instruction = encode(destination, source, count)
    source_value = (int(dut.gprs_o.value) >> (source * GPR_WIDTH)) & GPR_MASK
    expected_scalar = (source_value & SCALAR_MASK) >> (count + 32)
    expected = (old_rd & (GPR_MASK ^ SCALAR_MASK)) | expected_scalar
    old_pc = int(dut.pc_o.value)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.operation_o.value) == OPERATION_DSRL32
    assert int(dut.execute_complete_o.value) == 1
    assert int(dut.execute_writeback_value_o.value) == expected
    assert int(dut.retirement_pc_o.value) == old_pc
    assert int(dut.retirement_instruction_o.value) == instruction
    await edge(dut)
    dut.instruction_valid_i.value = 0
    await Timer(1, unit="ns")
    assert int(dut.pc_o.value) == (old_pc + 4) & 0xFFFF_FFFF
    actual = (int(dut.gprs_o.value) >> (destination * GPR_WIDTH)) & GPR_MASK
    assert actual == (0 if destination == 0 else expected)
    await edge(dut)
    return expected


@cocotb.test()
async def test_dsrl32_effective_counts_and_upper_lane(dut) -> None:
    """Cover effective shifts 32, 33, 62, and 63 without sign fill."""
    await initialize(dut, 0x1000)
    upper = 0x0123_4567_89AB_CDEF << 64
    for count, scalar, result in (
        (0, 0xFEDC_BA98_7654_3210, 0x0000_0000_FEDC_BA98),
        (1, 0xFEDC_BA98_7654_3210, 0x0000_0000_7F6E_5D4C),
        (30, 0xC000_0000_0000_0000, 3),
        (31, 0x8000_0000_0000_0000, 1),
    ):
        source = 0xDEAD_BEEF_CAFE_F00D_0000_0000_0000_0000 | scalar
        destination = upper | 0xAAAA_BBBB_CCCC_DDDD
        await seed_gpr(dut, 3, source)
        await seed_gpr(dut, 5, destination)
        assert await execute(dut, 5, 3, count, destination) == upper | result


@cocotb.test()
async def test_dsrl32_alias_zero_and_pc_wrap(dut) -> None:
    """Read before an aliased write and suppress destination zero."""
    await initialize(dut, 0xFFFF_FFF8)
    original = 0xCAFE_BABE_1234_5678_FEDC_BA98_7654_3210
    await seed_gpr(dut, 7, original)
    assert await execute(dut, 7, 7, 4, original) == ALIASED_DSRL32_RESULT
    await execute(dut, 0, 7, 31, 0)
    assert int(dut.pc_o.value) == 0


@cocotb.test()
async def test_dsrl32_encoding_and_reserved_rs(dut) -> None:
    """Check exact function encoding and reject nonzero reserved rs."""
    await initialize(dut, 0x4000)
    exact = encode(31, 17, 13)
    assert exact == ENCODED_DSRL32_EXAMPLE
    illegal = (1 << 21) | exact
    dut.instruction_valid_i.value = 1
    dut.instruction_i.value = illegal
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 0
    assert int(dut.reserved_valid_o.value) == 1
    assert int(dut.reserved_instruction_o.value) == illegal
