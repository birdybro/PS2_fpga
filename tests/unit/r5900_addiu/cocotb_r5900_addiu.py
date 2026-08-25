"""Directed architectural tests for R5900 ADDIU."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
SCALAR_MASK = (1 << 64) - 1
WORD_MASK = (1 << 32) - 1
OPERATION_ADDIU = 12


def encode_addiu(destination: int, source: int, immediate: int) -> int:
    return (0x09 << 26) | (source << 21) | (destination << 16) | immediate


def expected_addiu(old_destination: int, source_value: int, immediate: int) -> int:
    signed_immediate = immediate - (1 << 16) if immediate & 0x8000 else immediate
    word = ((source_value & WORD_MASK) + signed_immediate) & WORD_MASK
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


async def execute_addiu(
    dut,
    destination: int,
    source: int,
    immediate: int,
    operands: tuple[int, int],
) -> int:
    old_destination, source_value = operands
    instruction = encode_addiu(destination, source, immediate)
    expected = expected_addiu(old_destination, source_value, immediate)
    old_pc = int(dut.pc_o.value)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_ADDIU
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
async def test_r5900_addiu_signed_immediate_and_word_wrap_boundaries(dut) -> None:
    await initialize(dut, 0x1000)
    destination_upper = 0x0123_4567_89AB_CDEF << 64
    cases = (
        (0x0000_0000, 0x0000, 0x0000_0000_0000_0000),
        (0x0000_0000, 0x0001, 0x0000_0000_0000_0001),
        (0x0000_0000, 0x7FFF, 0x0000_0000_0000_7FFF),
        (0x0000_0000, 0x8000, 0xFFFF_FFFF_FFFF_8000),
        (0x0000_0000, 0xFFFF, 0xFFFF_FFFF_FFFF_FFFF),
        (0x7FFF_FFFF, 0x0001, 0xFFFF_FFFF_8000_0000),
        (0x8000_0000, 0xFFFF, 0x0000_0000_7FFF_FFFF),
        (0xFFFF_FFFF, 0x0001, 0x0000_0000_0000_0000),
    )
    for source_word, immediate, expected_scalar in cases:
        source_value = 0xFFFF_FFFF_FFFF_FFFF_1234_5678_0000_0000 | source_word
        old_destination = destination_upper | 0xAAAA_BBBB_CCCC_DDDD
        await seed_gpr(dut, 4, source_value)
        await seed_gpr(dut, 5, old_destination)
        expected = destination_upper | expected_scalar
        assert (
            await execute_addiu(dut, 5, 4, immediate, (old_destination, source_value)) == expected
        )


@cocotb.test()
async def test_r5900_addiu_source_destination_alias_ignores_source_high_bits(dut) -> None:
    await initialize(dut, 0x2000)
    aliased = 0xCAFE_BABE_1234_5678_AAAA_BBBB_7FFF_FFFF
    await seed_gpr(dut, 31, aliased)
    await execute_addiu(dut, 31, 31, 1, (aliased, aliased))
    zero_source_destination = 0x1111_2222_3333_4444_AAAA_BBBB_CCCC_DDDD
    await seed_gpr(dut, 7, zero_source_destination)
    await execute_addiu(dut, 7, 0, 0x8000, (zero_source_destination, 0))


@cocotb.test()
async def test_r5900_addiu_to_zero_retires_without_writeback_and_wraps_pc(dut) -> None:
    await initialize(dut, 0xFFFF_FFFC)
    source_value = 0x9999_AAAA_BBBB_CCCC_0123_4567_7FFF_FFFF
    await seed_gpr(dut, 9, source_value)
    await execute_addiu(dut, 0, 9, 1, (0, source_value))
    assert int(dut.pc_o.value) == 0
