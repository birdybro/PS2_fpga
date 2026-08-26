"""Directed architectural tests for R5900 MFHI1."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
SCALAR_MASK = (1 << 64) - 1
WORD_MASK = (1 << 32) - 1
OPERATION_NONE = 0
OPERATION_MFHI1 = 47
HI_SEED = 0x1111_2222_3333_4444
LO_SEED = 0x2222_3333_4444_5555
LO1_SEED = 0x9999_AAAA_BBBB_CCCC
RESERVED_TEST_PC = 0x3000


def encode_mfhi1(destination: int, reserved_rs_rt: int = 0, reserved_sa: int = 0) -> int:
    """Encode MFHI1 while allowing explicit reserved-field negative tests."""
    return (0x1C << 26) | (reserved_rs_rt << 16) | (destination << 11) | (reserved_sa << 6) | 0x10


async def edge(dut) -> None:
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut, start_pc: int, hi1_value: int) -> None:
    """Reset the harness and explicitly seed all accumulator fields."""
    dut.rst_ni.value = 0
    dut.start_pc_i.value = start_pc
    dut.instruction_valid_i.value = 0
    dut.instruction_i.value = 0
    dut.seed_gpr_commit_i.value = 0
    dut.seed_gpr_destination_i.value = 0
    dut.seed_gpr_value_i.value = 0
    dut.seed_hilo_commit_i.value = 0
    dut.seed_hi_i.value = HI_SEED
    dut.seed_lo_i.value = LO_SEED
    dut.seed_hi1_i.value = hi1_value
    dut.seed_lo1_i.value = LO1_SEED
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1
    dut.seed_hilo_commit_i.value = 1
    await edge(dut)
    dut.seed_hilo_commit_i.value = 0


async def seed_gpr(dut, destination: int, value: int) -> None:
    dut.seed_gpr_destination_i.value = destination
    dut.seed_gpr_value_i.value = value
    dut.seed_gpr_commit_i.value = 1
    await edge(dut)
    dut.seed_gpr_commit_i.value = 0
    await edge(dut)


async def seed_hi1(dut, value: int) -> None:
    """Change secondary HI1 while preserving explicitly supplied sibling fields."""
    dut.seed_hi1_i.value = value
    dut.seed_hilo_commit_i.value = 1
    await edge(dut)
    dut.seed_hilo_commit_i.value = 0
    await edge(dut)


async def execute_mfhi1(dut, destination: int, old_destination: int, hi1_value: int) -> int:
    """Execute one canonical MFHI1 and compare all events and architectural state."""
    instruction = encode_mfhi1(destination)
    expected_gpr = (old_destination & (GPR_MASK ^ SCALAR_MASK)) | hi1_value
    old_pc = int(dut.pc_o.value)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_MFHI1
    assert int(dut.execute_complete_o.value) == 1
    assert int(dut.pc_advance_o.value) == 1
    assert int(dut.execute_writeback_commit_o.value) == 1
    assert int(dut.execute_writeback_destination_o.value) == destination
    assert int(dut.execute_writeback_value_o.value) == expected_gpr
    assert int(dut.execute_write_hi_valid_o.value) == 0
    assert int(dut.execute_write_lo_valid_o.value) == 0
    assert int(dut.execute_write_hi1_valid_o.value) == 0
    assert int(dut.execute_write_lo1_valid_o.value) == 0
    assert int(dut.writeback_valid_o.value) == (destination != 0)
    assert int(dut.retirement_valid_o.value) == 1
    assert int(dut.retirement_pc_o.value) == old_pc
    assert int(dut.retirement_instruction_o.value) == instruction
    assert int(dut.reserved_valid_o.value) == 0
    await edge(dut)
    dut.instruction_valid_i.value = 0
    await Timer(1, unit="ns")
    actual = (int(dut.gprs_o.value) >> (destination * GPR_WIDTH)) & GPR_MASK
    assert actual == (0 if destination == 0 else expected_gpr)
    assert (int(dut.hi_o.value), int(dut.lo_o.value)) == (HI_SEED, LO_SEED)
    assert (int(dut.hi1_o.value), int(dut.lo1_o.value)) == (hi1_value, LO1_SEED)
    assert int(dut.pc_o.value) == (old_pc + 4) & WORD_MASK
    await edge(dut)
    return expected_gpr


@cocotb.test()
async def test_r5900_mfhi1_full_width_values_and_preserved_upper_lane(dut) -> None:
    """Transfer every 64-bit boundary class without scalar sign conversion."""
    await initialize(dut, 0x1000, 0)
    destination = 0xCAFE_BABE_1234_5678_AAAA_BBBB_CCCC_DDDD
    for hi1_value in (
        0,
        1,
        0x7FFF_FFFF,
        0x8000_0000,
        0xFFFF_FFFF,
        0x8000_0000_0000_0000,
        SCALAR_MASK,
        0x0123_4567_89AB_CDEF,
    ):
        await seed_hi1(dut, hi1_value)
        await seed_gpr(dut, 31, destination)
        await execute_mfhi1(dut, 31, destination, hi1_value)


@cocotb.test()
async def test_r5900_mfhi1_destination_zero_is_suppressed(dut) -> None:
    """Produce an rd-zero candidate while architectural GPR zero remains fixed."""
    hi1_value = 0xFEDC_BA98_7654_3210
    await initialize(dut, 0x2000, hi1_value)
    await execute_mfhi1(dut, 0, 0, hi1_value)


@cocotb.test()
async def test_r5900_mfhi1_wraps_pc_without_changing_hilo(dut) -> None:
    """Retire at the PC boundary while all four accumulator fields hold."""
    hi1_value = 0x8000_0000_0000_0001
    await initialize(dut, 0xFFFF_FFFC, hi1_value)
    destination = 0xAAAA_BBBB_CCCC_DDDD_1111_2222_3333_4444
    await seed_gpr(dut, 1, destination)
    await execute_mfhi1(dut, 1, destination, hi1_value)
    assert int(dut.pc_o.value) == 0


@cocotb.test()
async def test_r5900_mfhi1_rejects_nonzero_reserved_fields(dut) -> None:
    """Reject populated rs, rt, or sa while preserving state and PC."""
    hi1_value = 0x0123_4567_89AB_CDEF
    await initialize(dut, RESERVED_TEST_PC, hi1_value)
    for instruction in (
        encode_mfhi1(5, reserved_rs_rt=1),
        encode_mfhi1(5, reserved_rs_rt=1 << 5),
        encode_mfhi1(5, reserved_rs_rt=0x3FF),
        encode_mfhi1(5, reserved_sa=1),
        encode_mfhi1(5, reserved_sa=31),
    ):
        dut.instruction_i.value = instruction
        dut.instruction_valid_i.value = 1
        await Timer(1, unit="ns")
        assert int(dut.execute_valid_o.value) == 0
        assert int(dut.operation_o.value) == OPERATION_NONE
        assert int(dut.execute_complete_o.value) == 0
        assert int(dut.execute_writeback_commit_o.value) == 0
        assert int(dut.reserved_valid_o.value) == 1
        assert int(dut.reserved_pc_o.value) == RESERVED_TEST_PC
        assert int(dut.reserved_instruction_o.value) == instruction
