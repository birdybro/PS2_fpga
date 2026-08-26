"""Directed architectural tests for R5900 DSRAV."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
SCALAR_MASK = (1 << 64) - 1
SCALAR_SIGN = 1 << 63
OPERATION_DSRAV = 31
ENCODED_DSRAV_EXAMPLE = 0x0131_F817


def encode(destination: int, source: int, shift_register: int) -> int:
    return (shift_register << 21) | (source << 16) | (destination << 11) | 0x17


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


async def execute(
    dut,
    destination: int,
    source: int,
    shift_register: int,
    old_rd: int,
) -> int:
    instruction = encode(destination, source, shift_register)
    packed_gprs = int(dut.gprs_o.value)
    source_value = (packed_gprs >> (source * GPR_WIDTH)) & SCALAR_MASK
    signed_source = source_value - (1 << 64) if source_value & SCALAR_SIGN else source_value
    count_value = (packed_gprs >> (shift_register * GPR_WIDTH)) & GPR_MASK
    expected_scalar = (signed_source >> (count_value & 0x3F)) & SCALAR_MASK
    expected = (old_rd & (GPR_MASK ^ SCALAR_MASK)) | expected_scalar
    old_pc = int(dut.pc_o.value)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.operation_o.value) == OPERATION_DSRAV
    assert int(dut.execute_complete_o.value) == 1
    assert int(dut.source_rs_value_o.value) == count_value
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
async def test_dsrav_masks_six_count_bits_sign_fills_and_preserves_upper(dut) -> None:
    """Cover both signs and counts 0, 1, 31, 32, 63, 64, and all ones."""
    await initialize(dut, 0x1000)
    upper = 0x0123_4567_89AB_CDEF << 64
    for count, scalar, result in (
        (0, 0x8000_0000_0000_0001, 0x8000_0000_0000_0001),
        (1, 0x8000_0000_0000_0001, 0xC000_0000_0000_0000),
        (31, 0x8000_0000_8000_0001, 0xFFFF_FFFF_0000_0001),
        (32, 0x8000_0000_8000_0001, 0xFFFF_FFFF_8000_0000),
        (63, 0x8000_0000_0000_0000, 0xFFFF_FFFF_FFFF_FFFF),
        (64, 0x8000_0000_0000_0001, 0x8000_0000_0000_0001),
        (GPR_MASK, 0x7FFF_FFFF_FFFF_FFFF, 0),
    ):
        source_value = 0xDEAD_BEEF_CAFE_F00D_0000_0000_0000_0000 | scalar
        destination_value = upper | 0xAAAA_BBBB_CCCC_DDDD
        await seed_gpr(dut, 2, count)
        await seed_gpr(dut, 3, source_value)
        await seed_gpr(dut, 5, destination_value)
        assert await execute(dut, 5, 3, 2, destination_value) == upper | result


@cocotb.test()
async def test_dsrav_aliases_zero_and_pc_wrap(dut) -> None:
    """Read every operand before aliased writeback and suppress destination zero."""
    await initialize(dut, 0xFFFF_FFF0)
    upper_mask = GPR_MASK ^ SCALAR_MASK
    original = 0xCAFE_BABE_1234_5678_FEDC_BA98_7654_3210
    await seed_gpr(dut, 2, 4)
    await seed_gpr(dut, 7, original)
    assert await execute(dut, 7, 7, 2, original) == (
        (original & upper_mask) | 0xFFED_CBA9_8765_4321
    )

    count_destination = 0x0123_4567_89AB_CDEF_1111_2222_0000_0021
    await seed_gpr(dut, 8, 0xFEDC_BA98_7654_3210)
    await seed_gpr(dut, 9, count_destination)
    assert await execute(dut, 9, 8, 9, count_destination) == (
        (count_destination & upper_mask) | 0xFFFF_FFFF_FF6E_5D4C
    )

    await seed_gpr(dut, 10, 3)
    assert await execute(dut, 11, 10, 10, 0) == 0
    await execute(dut, 0, 7, 2, 0)
    assert int(dut.pc_o.value) == 0


@cocotb.test()
async def test_dsrav_encoding_and_reserved_sa(dut) -> None:
    """Check exact function encoding and reject nonzero reserved sa."""
    await initialize(dut, 0x4000)
    exact = encode(31, 17, 9)
    assert exact == ENCODED_DSRAV_EXAMPLE
    illegal = exact | (1 << 6)
    dut.instruction_valid_i.value = 1
    dut.instruction_i.value = illegal
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 0
    assert int(dut.reserved_valid_o.value) == 1
    assert int(dut.reserved_instruction_o.value) == illegal
