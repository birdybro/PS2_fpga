"""Directed architectural tests for R5900 64-bit DSRL."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
SCALAR_MASK = (1 << 64) - 1
OPERATION_DSRL = 24
DOUBLEWORD_SHIFT_RESULT = 0x0123_4567_89AB_CDEF_4000_0000_0000_0000
ALIASED_DSRL_RESULT = 0xCAFE_BABE_1234_5678_0876_5432_1800_0001
ENCODED_DSRL_EXAMPLE = 0x0011_FB7A


def encode_dsrl(destination: int, source: int, shift_amount: int) -> int:
    """Build canonical SPECIAL DSRL independently of the Python model."""
    return (source << 16) | (destination << 11) | (shift_amount << 6) | 0x3A


def dsrl_result(source: int, old_destination: int, shift_amount: int) -> int:
    """Form a logical low-doubleword shift and explicit destination merge."""
    shifted_scalar = (source & SCALAR_MASK) >> shift_amount
    return (old_destination & (GPR_MASK ^ SCALAR_MASK)) | shifted_scalar


async def edge(dut) -> None:
    """Advance one rising edge and settle architectural state."""
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut, start_pc: int) -> None:
    """Start the clock and reset the immediate-shift harness."""
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
    """Initialize one nonzero GPR through the shared writeback path."""
    dut.seed_destination_i.value = destination
    dut.seed_value_i.value = value
    dut.seed_commit_i.value = 1
    await edge(dut)
    dut.seed_commit_i.value = 0
    await edge(dut)


async def execute_dsrl(
    dut,
    *,
    instruction: int,
    expected_source: int,
    old_destination: int,
) -> int:
    """Check one complete DSRL transaction and return the expected destination."""
    destination = (instruction >> 11) & 0x1F
    shift_amount = (instruction >> 6) & 0x1F
    expected = dsrl_result(expected_source, old_destination, shift_amount)
    old_pc = int(dut.pc_o.value)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")

    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_DSRL
    assert int(dut.execute_complete_o.value) == 1
    assert int(dut.pc_advance_o.value) == 1
    assert int(dut.source_rt_value_o.value) == expected_source
    assert int(dut.destination_value_o.value) == (0 if destination == 0 else old_destination)
    assert int(dut.execute_writeback_commit_o.value) == 1
    assert int(dut.execute_writeback_destination_o.value) == destination
    assert int(dut.execute_writeback_value_o.value) == expected
    assert int(dut.commit_accepted_o.value) == 1
    assert int(dut.writeback_valid_o.value) == (destination != 0)
    assert int(dut.writeback_destination_o.value) == (destination if destination else 0)
    assert int(dut.writeback_value_o.value) == (expected if destination else 0)
    assert int(dut.retirement_valid_o.value) == 1
    assert int(dut.retirement_pc_o.value) == old_pc
    assert int(dut.retirement_instruction_o.value) == instruction
    assert int(dut.reserved_valid_o.value) == 0

    await edge(dut)
    dut.instruction_valid_i.value = 0
    await Timer(1, unit="ns")
    assert int(dut.pc_o.value) == (old_pc + 4) & 0xFFFF_FFFF
    actual_destination = (int(dut.gprs_o.value) >> (destination * GPR_WIDTH)) & GPR_MASK
    assert actual_destination == (0 if destination == 0 else expected)
    assert int(dut.retirement_valid_o.value) == 0
    await edge(dut)
    return expected


@cocotb.test()
async def test_r5900_dsrl_logically_shifts_low_doubleword_and_preserves_upper_lane(dut) -> None:
    """Ignore source high bits, zero-fill all 64 scalar bits, and retain rd upper bits."""
    await initialize(dut, 0x0010_0000)
    source = 0xFEDC_BA98_7654_3210_8000_0000_0000_0001
    destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
    await seed_gpr(dut, 3, source)
    await seed_gpr(dut, 5, destination)
    result = await execute_dsrl(
        dut,
        instruction=encode_dsrl(5, 3, 1),
        expected_source=source,
        old_destination=destination,
    )
    assert result == DOUBLEWORD_SHIFT_RESULT


@cocotb.test()
async def test_r5900_dsrl_covers_zero_one_thirty_and_thirty_one_counts(dut) -> None:
    """Cover count boundaries, zero fill, and fully shifted-out low bits."""
    await initialize(dut, 0x2000)
    upper = 0xA55A_6996_0FF0_F00F << 64
    cases = (
        (0, 0xFEDC_BA98_7654_3210, 0xFEDC_BA98_7654_3210),
        (1, 0x8000_0000_0000_0001, 0x4000_0000_0000_0000),
        (30, 0xC000_0000_0000_0003, 0x0000_0003_0000_0000),
        (31, 0x8000_0000_8000_0001, 0x0000_0001_0000_0001),
        (31, 0x0000_0000_0000_0001, 0),
    )
    for shift_amount, scalar, expected_scalar in cases:
        source = 0xDEAD_BEEF_CAFE_F00D_0000_0000_0000_0000 | scalar
        destination = upper | 0x1111_2222_3333_4444
        await seed_gpr(dut, 8, source)
        await seed_gpr(dut, 9, destination)
        result = await execute_dsrl(
            dut,
            instruction=encode_dsrl(9, 8, shift_amount),
            expected_source=source,
            old_destination=destination,
        )
        assert result == upper | expected_scalar


@cocotb.test()
async def test_r5900_dsrl_reads_before_aliasing_destination_write(dut) -> None:
    """Use original low and upper lanes when rd aliases rt."""
    await initialize(dut, 0x3000)
    original = 0xCAFE_BABE_1234_5678_8765_4321_8000_0010
    await seed_gpr(dut, 7, original)
    result = await execute_dsrl(
        dut,
        instruction=encode_dsrl(7, 7, 4),
        expected_source=original,
        old_destination=original,
    )
    assert result == ALIASED_DSRL_RESULT


@cocotb.test()
async def test_r5900_dsrl_to_zero_retires_without_architectural_writeback(dut) -> None:
    """Complete DSRL while the centralized writeback boundary protects GPR zero."""
    await initialize(dut, 0xFFFF_FFFC)
    source = 0xFFFF_FFFF_FFFF_FFFF_8000_0000_0000_0000
    await seed_gpr(dut, 4, source)
    await execute_dsrl(
        dut,
        instruction=encode_dsrl(0, 4, 31),
        expected_source=source,
        old_destination=0,
    )
    assert int(dut.pc_o.value) == 0


@cocotb.test()
async def test_r5900_dsrl_exact_encoding_and_reserved_rs_remain_distinct(dut) -> None:
    """Admit function 0x3a only when its architecturally reserved rs field is zero."""
    await initialize(dut, 0x4000)
    exact = encode_dsrl(31, 17, 13)
    assert exact == ENCODED_DSRL_EXAMPLE
    dut.instruction_valid_i.value = 1
    dut.instruction_i.value = exact
    await Timer(1, unit="ns")
    assert int(dut.operation_o.value) == OPERATION_DSRL
    dut.instruction_valid_i.value = 0
    await Timer(1, unit="ns")

    illegal = (1 << 21) | exact
    old_pc = int(dut.pc_o.value)
    dut.instruction_valid_i.value = 1
    dut.instruction_i.value = illegal
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 0
    assert int(dut.execute_complete_o.value) == 0
    assert int(dut.pc_advance_o.value) == 0
    assert int(dut.execute_writeback_commit_o.value) == 0
    assert int(dut.retirement_valid_o.value) == 0
    assert int(dut.reserved_valid_o.value) == 1
    assert int(dut.reserved_pc_o.value) == old_pc
    assert int(dut.reserved_instruction_o.value) == illegal
    await edge(dut)
    assert int(dut.pc_o.value) == old_pc
