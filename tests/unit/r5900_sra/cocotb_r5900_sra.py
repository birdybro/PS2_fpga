"""Directed architectural tests for R5900 32-bit SRA."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
SCALAR_MASK = (1 << 64) - 1
WORD_MASK = (1 << 32) - 1
OPERATION_SRL = 3
OPERATION_SRA = 4
ARITHMETIC_SHIFT_RESULT = 0x0123_4567_89AB_CDEF_FFFF_FFFF_C000_0000


def encode_sra(destination: int, source: int, shift_amount: int) -> int:
    """Build a canonical SPECIAL SRA instruction independently of the model."""
    return (source << 16) | (destination << 11) | (shift_amount << 6) | 3


def sra_result(source: int, old_destination: int, shift_amount: int) -> int:
    """Form the expected SRA result using an explicit signed Python word."""
    signed_word = source & WORD_MASK
    if signed_word & (1 << 31):
        signed_word -= 1 << 32
    word = (signed_word >> shift_amount) & WORD_MASK
    scalar = word | ((SCALAR_MASK ^ WORD_MASK) if word & (1 << 31) else 0)
    return (old_destination & (GPR_MASK ^ SCALAR_MASK)) | scalar


async def edge(dut) -> None:
    """Advance one rising edge and settle architectural state."""
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut, start_pc: int) -> None:
    """Start the clock and reset the shared immediate-shift harness."""
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


async def execute_sra(
    dut,
    *,
    instruction: int,
    expected_source: int,
    old_destination: int,
) -> int:
    """Check one complete SRA transaction and return its expected destination."""
    destination = (instruction >> 11) & 0x1F
    shift_amount = (instruction >> 6) & 0x1F
    expected = sra_result(expected_source, old_destination, shift_amount)
    old_pc = int(dut.pc_o.value)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")

    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_SRA
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
    await edge(dut)
    return expected


@cocotb.test()
async def test_r5900_sra_sign_fills_and_preserves_destination_upper_lane(dut) -> None:
    """Ignore source high bits, shift in the sign bit, and retain rd bits 127:64."""
    await initialize(dut, 0x0010_0000)
    source = 0xFEDC_BA98_7654_3210_1111_2222_8000_0001
    destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
    await seed_gpr(dut, 3, source)
    await seed_gpr(dut, 5, destination)
    result = await execute_sra(
        dut,
        instruction=encode_sra(5, 3, 1),
        expected_source=source,
        old_destination=destination,
    )
    assert result == ARITHMETIC_SHIFT_RESULT


@cocotb.test()
async def test_r5900_sra_covers_signed_boundary_counts(dut) -> None:
    """Cover counts zero, one, thirty, and thirty-one for both source signs."""
    await initialize(dut, 0x2000)
    upper = 0xA55A_6996_0FF0_F00F << 64
    cases = (
        (0, 0x7FFF_FFFF, 0x0000_0000_7FFF_FFFF),
        (0, 0x8000_0000, 0xFFFF_FFFF_8000_0000),
        (1, 0x8000_0000, 0xFFFF_FFFF_C000_0000),
        (30, 0x8000_0000, 0xFFFF_FFFF_FFFF_FFFE),
        (31, 0x8000_0000, 0xFFFF_FFFF_FFFF_FFFF),
        (31, 0x7FFF_FFFF, 0x0000_0000_0000_0000),
    )
    for shift_amount, low_word, expected_scalar in cases:
        source = 0xDEAD_BEEF_CAFE_F00D_1234_5678_0000_0000 | low_word
        destination = upper | 0x1111_2222_3333_4444
        await seed_gpr(dut, 8, source)
        await seed_gpr(dut, 9, destination)
        result = await execute_sra(
            dut,
            instruction=encode_sra(9, 8, shift_amount),
            expected_source=source,
            old_destination=destination,
        )
        assert result == upper | expected_scalar


@cocotb.test()
async def test_r5900_sra_reads_before_aliased_destination_write(dut) -> None:
    """Use the original signed source word and upper lane when rd equals rt."""
    await initialize(dut, 0x3000)
    original = 0xCAFE_BABE_1234_5678_8765_4321_8000_0010
    await seed_gpr(dut, 7, original)
    await execute_sra(
        dut,
        instruction=encode_sra(7, 7, 4),
        expected_source=original,
        old_destination=original,
    )


@cocotb.test()
async def test_r5900_sra_to_zero_retires_without_architectural_writeback(dut) -> None:
    """Complete legal SRA while the centralized boundary protects GPR zero."""
    await initialize(dut, 0xFFFF_FFFC)
    source = 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_8000_0000
    await seed_gpr(dut, 4, source)
    await execute_sra(
        dut,
        instruction=encode_sra(0, 4, 31),
        expected_source=source,
        old_destination=0,
    )
    assert int(dut.pc_o.value) == 0


@cocotb.test()
async def test_r5900_sra_is_distinct_from_srl_and_rejects_reserved_rs(dut) -> None:
    """Keep logical and arithmetic operations distinct and reject reserved rs."""
    await initialize(dut, 0x4000)
    dut.instruction_valid_i.value = 1
    dut.instruction_i.value = (2 << 16) | (3 << 11) | (1 << 6) | 2
    await Timer(1, unit="ns")
    assert int(dut.operation_o.value) == OPERATION_SRL
    dut.instruction_valid_i.value = 0
    await Timer(1, unit="ns")

    illegal = (1 << 21) | encode_sra(3, 2, 1)
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
