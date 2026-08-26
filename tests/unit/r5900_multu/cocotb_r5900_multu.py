"""Directed architectural tests for R5900 MULTU."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
SCALAR_MASK = (1 << 64) - 1
WORD_MASK = (1 << 32) - 1
OPERATION_NONE = 0
OPERATION_MULTU = 36
HI1_SEED = 0x3333_4444_5555_6666
LO1_SEED = 0x7777_8888_9999_AAAA
RESERVED_TEST_PC = 0x3000


def encode_multu(destination: int, source_a: int, source_b: int, shift: int = 0) -> int:
    return (source_a << 21) | (source_b << 16) | (destination << 11) | (shift << 6) | 0x19


def sign_extend_word(value: int) -> int:
    word = value & WORD_MASK
    return word | ((SCALAR_MASK ^ WORD_MASK) if word & (1 << 31) else 0)


def expected_product(source_a_value: int, source_b_value: int) -> tuple[int, int]:
    product = ((source_a_value & WORD_MASK) * (source_b_value & WORD_MASK)) & SCALAR_MASK
    return sign_extend_word(product >> 32), sign_extend_word(product)


async def edge(dut) -> None:
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut, start_pc: int) -> None:
    dut.rst_ni.value = 0
    dut.start_pc_i.value = start_pc
    dut.instruction_valid_i.value = 0
    dut.instruction_i.value = 0
    dut.seed_gpr_commit_i.value = 0
    dut.seed_gpr_destination_i.value = 0
    dut.seed_gpr_value_i.value = 0
    dut.seed_hilo_commit_i.value = 0
    dut.seed_hi_i.value = 0
    dut.seed_lo_i.value = 0
    dut.seed_hi1_i.value = 0
    dut.seed_lo1_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1
    dut.seed_hilo_commit_i.value = 1
    dut.seed_hi_i.value = 0x1111
    dut.seed_lo_i.value = 0x2222
    dut.seed_hi1_i.value = HI1_SEED
    dut.seed_lo1_i.value = LO1_SEED
    await edge(dut)
    dut.seed_hilo_commit_i.value = 0


async def seed_gpr(dut, destination: int, value: int) -> None:
    dut.seed_gpr_destination_i.value = destination
    dut.seed_gpr_value_i.value = value
    dut.seed_gpr_commit_i.value = 1
    await edge(dut)
    dut.seed_gpr_commit_i.value = 0
    await edge(dut)


async def execute_multu(
    dut,
    fields: tuple[int, int, int],
    old_destination: int,
    source_values: tuple[int, int],
) -> tuple[int, int]:
    destination, source_a, source_b = fields
    source_a_value, source_b_value = source_values
    instruction = encode_multu(destination, source_a, source_b)
    expected_hi, expected_lo = expected_product(source_a_value, source_b_value)
    expected_gpr = (old_destination & (GPR_MASK ^ SCALAR_MASK)) | expected_lo
    old_pc = int(dut.pc_o.value)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_MULTU
    assert int(dut.execute_complete_o.value) == 1
    assert int(dut.execute_write_hi_valid_o.value) == 1
    assert int(dut.execute_write_hi_value_o.value) == expected_hi
    assert int(dut.execute_write_lo_valid_o.value) == 1
    assert int(dut.execute_write_lo_value_o.value) == expected_lo
    assert int(dut.execute_writeback_commit_o.value) == (destination != 0)
    assert int(dut.execute_writeback_destination_o.value) == destination
    assert int(dut.execute_writeback_value_o.value) == expected_gpr
    assert int(dut.writeback_valid_o.value) == (destination != 0)
    assert int(dut.retirement_valid_o.value) == 1
    assert int(dut.retirement_pc_o.value) == old_pc
    assert int(dut.retirement_instruction_o.value) == instruction
    await edge(dut)
    dut.instruction_valid_i.value = 0
    await Timer(1, unit="ns")
    actual_gpr = (int(dut.gprs_o.value) >> (destination * GPR_WIDTH)) & GPR_MASK
    assert actual_gpr == (0 if destination == 0 else expected_gpr)
    assert (int(dut.hi_o.value), int(dut.lo_o.value)) == (expected_hi, expected_lo)
    assert (int(dut.hi1_o.value), int(dut.lo1_o.value)) == (HI1_SEED, LO1_SEED)
    assert int(dut.pc_o.value) == (old_pc + 4) & WORD_MASK
    await edge(dut)
    return expected_hi, expected_lo


@cocotb.test()
async def test_r5900_multu_unsigned_extrema_and_signed_half_extension(dut) -> None:
    await initialize(dut, 0x1000)
    cases = (
        (0x0000_0000, 0xFFFF_FFFF, 0, 0),
        (0x0000_0001, 0x0000_0001, 0, 1),
        (0xFFFF_FFFF, 0x0000_0001, 0, SCALAR_MASK),
        (0xFFFF_FFFF, 0xFFFF_FFFF, 0xFFFF_FFFF_FFFF_FFFE, 1),
        (0x7FFF_FFFF, 0x0000_0002, 0, 0xFFFF_FFFF_FFFF_FFFE),
        (0x8000_0000, 0x0000_0001, 0, 0xFFFF_FFFF_8000_0000),
        (0x8000_0000, 0xFFFF_FFFF, 0x0000_0000_7FFF_FFFF, 0xFFFF_FFFF_8000_0000),
        (0x8000_0000, 0x8000_0000, 0x0000_0000_4000_0000, 0),
    )
    for source_a_word, source_b_word, expected_hi, expected_lo in cases:
        source_a = 0xDEAD_BEEF_CAFE_F00D_1234_5678_0000_0000 | source_a_word
        source_b = 0xAAAA_5555_AAAA_5555_8765_4321_0000_0000 | source_b_word
        destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
        await seed_gpr(dut, 3, source_a)
        await seed_gpr(dut, 4, source_b)
        await seed_gpr(dut, 5, destination)
        assert await execute_multu(dut, (5, 3, 4), destination, (source_a, source_b)) == (
            expected_hi,
            expected_lo,
        )


@cocotb.test()
async def test_r5900_multu_optional_destination_zero_still_updates_hilo(dut) -> None:
    await initialize(dut, 0x2000)
    source_a = 0xAAAA_BBBB_CCCC_DDDD_FFFF_FFFF_FFFF_FFFF
    source_b = 0x1111_2222_3333_4444_0000_0000_0000_0001
    await seed_gpr(dut, 8, source_a)
    await seed_gpr(dut, 9, source_b)
    await execute_multu(dut, (0, 8, 9), 0, (source_a, source_b))


@cocotb.test()
async def test_r5900_multu_optional_destination_aliases_source_and_wraps_pc(dut) -> None:
    await initialize(dut, 0xFFFF_FFFC)
    source = 0xCAFE_BABE_1234_5678_FFFF_FFFF_FFFF_FFFF
    await seed_gpr(dut, 31, source)
    await execute_multu(dut, (31, 31, 31), source, (source, source))
    assert int(dut.pc_o.value) == 0


@cocotb.test()
async def test_r5900_multu_rejects_nonzero_reserved_shift_field(dut) -> None:
    await initialize(dut, RESERVED_TEST_PC)
    instruction = encode_multu(5, 3, 4, shift=1)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 0
    assert int(dut.operation_o.value) == OPERATION_NONE
    assert int(dut.execute_complete_o.value) == 0
    assert int(dut.execute_write_hi_valid_o.value) == 0
    assert int(dut.execute_write_lo_valid_o.value) == 0
    assert int(dut.reserved_valid_o.value) == 1
    assert int(dut.reserved_pc_o.value) == RESERVED_TEST_PC
    assert int(dut.reserved_instruction_o.value) == instruction
