"""Directed architectural tests for R5900 32-bit SRAV."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
SCALAR_MASK = (1 << 64) - 1
WORD_MASK = (1 << 32) - 1
OPERATION_SRLV = 6
OPERATION_SRAV = 7
MASKED_SHIFT_RESULT = 0x0123_4567_89AB_CDEF_FFFF_FFFF_C000_0000


def encode_srav(destination: int, source: int, shift_register: int) -> int:
    """Build canonical SPECIAL SRAV independently from the Python model."""
    return (shift_register << 21) | (source << 16) | (destination << 11) | 7


def srav_result(source: int, old_destination: int, shift_register: int) -> int:
    """Form expected SRAV data by explicitly converting the source word to signed."""
    signed_word = source & WORD_MASK
    if signed_word & (1 << 31):
        signed_word -= 1 << 32
    word = (signed_word >> (shift_register & 0x1F)) & WORD_MASK
    scalar = word | ((SCALAR_MASK ^ WORD_MASK) if word & (1 << 31) else 0)
    return (old_destination & (GPR_MASK ^ SCALAR_MASK)) | scalar


async def edge(dut) -> None:
    """Advance one rising edge and settle architectural state."""
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut, start_pc: int) -> None:
    """Start the clock and reset the shared shift harness."""
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


async def execute_srav(
    dut,
    *,
    instruction: int,
    expected_shift_register: int,
    expected_source: int,
    old_destination: int,
) -> int:
    """Check one complete SRAV transaction and return its expected destination."""
    destination = (instruction >> 11) & 0x1F
    expected = srav_result(expected_source, old_destination, expected_shift_register)
    old_pc = int(dut.pc_o.value)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")

    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_SRAV
    assert int(dut.execute_complete_o.value) == 1
    assert int(dut.pc_advance_o.value) == 1
    assert int(dut.source_rs_value_o.value) == expected_shift_register
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
    await edge(dut)
    return expected


@cocotb.test()
async def test_r5900_srav_sign_fills_using_only_low_five_count_bits(dut) -> None:
    """Ignore high count and data bits while preserving destination bits 127:64."""
    await initialize(dut, 0x0010_0000)
    shift_register = 0xFFFF_EEEE_DDDD_CCCC_BBBB_AAAA_0000_0021
    source = 0xFEDC_BA98_7654_3210_1111_2222_8000_0001
    destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
    await seed_gpr(dut, 2, shift_register)
    await seed_gpr(dut, 3, source)
    await seed_gpr(dut, 5, destination)
    result = await execute_srav(
        dut,
        instruction=encode_srav(5, 3, 2),
        expected_shift_register=shift_register,
        expected_source=source,
        old_destination=destination,
    )
    assert result == MASKED_SHIFT_RESULT


@cocotb.test()
async def test_r5900_srav_covers_signed_masked_count_boundaries(dut) -> None:
    """Cover both signs and effective counts zero, one, thirty, and thirty-one."""
    await initialize(dut, 0x2000)
    upper = 0xA55A_6996_0FF0_F00F << 64
    cases = (
        (0, 0x8000_0001, 0xFFFF_FFFF_8000_0001),
        (1, 0x8000_0001, 0xFFFF_FFFF_C000_0000),
        (30, 0x8000_0000, 0xFFFF_FFFF_FFFF_FFFE),
        (31, 0x8000_0001, 0xFFFF_FFFF_FFFF_FFFF),
        (31, 0x7FFF_FFFF, 0x0000_0000_0000_0000),
        (32, 0x8000_0001, 0xFFFF_FFFF_8000_0001),
        (33, 0x8000_0001, 0xFFFF_FFFF_C000_0000),
        (0xFFFF_FFFF, 0x8000_0001, 0xFFFF_FFFF_FFFF_FFFF),
    )
    for count, low_word, expected_scalar in cases:
        shift_register = 0xDEAD_BEEF_CAFE_F00D_1234_5678_0000_0000 | count
        source = 0xAAAA_BBBB_CCCC_DDDD_1111_2222_0000_0000 | low_word
        destination = upper | 0x1111_2222_3333_4444
        await seed_gpr(dut, 7, shift_register)
        await seed_gpr(dut, 8, source)
        await seed_gpr(dut, 9, destination)
        result = await execute_srav(
            dut,
            instruction=encode_srav(9, 8, 7),
            expected_shift_register=shift_register,
            expected_source=source,
            old_destination=destination,
        )
        assert result == upper | expected_scalar


@cocotb.test()
async def test_r5900_srav_reads_before_rt_or_rs_alias_write(dut) -> None:
    """Use original values when rd aliases either the data or count register."""
    await initialize(dut, 0x3000)
    source_and_destination = 0xCAFE_BABE_1234_5678_8765_4321_8000_0010
    await seed_gpr(dut, 2, 4)
    await seed_gpr(dut, 7, source_and_destination)
    await execute_srav(
        dut,
        instruction=encode_srav(7, 7, 2),
        expected_shift_register=4,
        expected_source=source_and_destination,
        old_destination=source_and_destination,
    )

    count_and_destination = 0x0123_4567_89AB_CDEF_1111_2222_0000_0021
    source = 0xFEDC_BA98_7654_3210_1111_2222_8000_0000
    await seed_gpr(dut, 8, source)
    await seed_gpr(dut, 9, count_and_destination)
    await execute_srav(
        dut,
        instruction=encode_srav(9, 8, 9),
        expected_shift_register=count_and_destination,
        expected_source=source,
        old_destination=count_and_destination,
    )


@cocotb.test()
async def test_r5900_srav_to_zero_retires_without_architectural_writeback(dut) -> None:
    """Complete legal SRAV while the centralized boundary protects GPR zero."""
    await initialize(dut, 0xFFFF_FFFC)
    await seed_gpr(dut, 2, 31)
    await seed_gpr(dut, 3, 0x8000_0001)
    await execute_srav(
        dut,
        instruction=encode_srav(0, 3, 2),
        expected_shift_register=31,
        expected_source=0x8000_0001,
        old_destination=0,
    )
    assert int(dut.pc_o.value) == 0


@cocotb.test()
async def test_r5900_srav_is_distinct_and_rejects_reserved_sa(dut) -> None:
    """Keep SRLV distinct and reject a nonzero reserved shift field."""
    await initialize(dut, 0x4000)
    dut.instruction_valid_i.value = 1
    dut.instruction_i.value = encode_srav(3, 2, 1) ^ 1
    await Timer(1, unit="ns")
    assert int(dut.operation_o.value) == OPERATION_SRLV
    dut.instruction_valid_i.value = 0
    await Timer(1, unit="ns")

    illegal = encode_srav(3, 2, 1) | (1 << 6)
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
