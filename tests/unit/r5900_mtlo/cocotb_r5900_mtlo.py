"""Directed architectural tests for R5900 MTLO."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
SCALAR_MASK = (1 << 64) - 1
WORD_MASK = (1 << 32) - 1
OPERATION_NONE = 0
OPERATION_MTLO = 42
HI_SEED = 0x1111_2222_3333_4444
INITIAL_LO = 0x2222_3333_4444_5555
HI1_SEED = 0x5555_6666_7777_8888
LO1_SEED = 0x9999_AAAA_BBBB_CCCC
RESERVED_TEST_PC = 0x3000


def encode_mtlo(source: int, reserved_rt_rd: int = 0, reserved_sa: int = 0) -> int:
    """Encode MTLO while allowing explicit reserved-field negative tests."""
    return (source << 21) | (reserved_rt_rd << 11) | (reserved_sa << 6) | 0x13


async def edge(dut) -> None:
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut, start_pc: int) -> None:
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
    dut.seed_lo_i.value = INITIAL_LO
    dut.seed_hi1_i.value = HI1_SEED
    dut.seed_lo1_i.value = LO1_SEED
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1
    dut.seed_hilo_commit_i.value = 1
    await edge(dut)
    dut.seed_hilo_commit_i.value = 0


async def seed_gpr(dut, source: int, value: int) -> None:
    dut.seed_gpr_destination_i.value = source
    dut.seed_gpr_value_i.value = value
    dut.seed_gpr_commit_i.value = 1
    await edge(dut)
    dut.seed_gpr_commit_i.value = 0
    await edge(dut)


async def execute_mtlo(dut, source: int, source_value: int) -> None:
    """Execute one canonical MTLO and compare all events and architectural state."""
    instruction = encode_mtlo(source)
    expected_lo = source_value & SCALAR_MASK if source else 0
    old_pc = int(dut.pc_o.value)
    old_gprs = int(dut.gprs_o.value)
    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_MTLO
    assert int(dut.execute_complete_o.value) == 1
    assert int(dut.pc_advance_o.value) == 1
    assert int(dut.execute_writeback_commit_o.value) == 0
    assert int(dut.execute_writeback_destination_o.value) == 0
    assert int(dut.execute_writeback_value_o.value) == 0
    assert int(dut.execute_write_hi_valid_o.value) == 0
    assert int(dut.execute_write_lo_valid_o.value) == 1
    assert int(dut.execute_write_lo_value_o.value) == expected_lo
    assert int(dut.writeback_valid_o.value) == 0
    assert int(dut.retirement_valid_o.value) == 1
    assert int(dut.retirement_pc_o.value) == old_pc
    assert int(dut.retirement_instruction_o.value) == instruction
    assert int(dut.reserved_valid_o.value) == 0
    await edge(dut)
    dut.instruction_valid_i.value = 0
    await Timer(1, unit="ns")
    assert int(dut.gprs_o.value) == old_gprs
    assert (int(dut.hi_o.value), int(dut.lo_o.value)) == (HI_SEED, expected_lo)
    assert (int(dut.hi1_o.value), int(dut.lo1_o.value)) == (HI1_SEED, LO1_SEED)
    assert int(dut.pc_o.value) == (old_pc + 4) & WORD_MASK
    await edge(dut)


@cocotb.test()
async def test_r5900_mtlo_full_width_values_and_ignored_upper_lane(dut) -> None:
    """Transfer every 64-bit boundary class without using GPR bits 127:64."""
    await initialize(dut, 0x1000)
    upper = 0xCAFE_BABE_1234_5678 << 64
    for scalar in (
        0,
        1,
        0x7FFF_FFFF,
        0x8000_0000,
        0xFFFF_FFFF,
        0x8000_0000_0000_0000,
        SCALAR_MASK,
        0x0123_4567_89AB_CDEF,
    ):
        source_value = upper | scalar
        await seed_gpr(dut, 31, source_value)
        await execute_mtlo(dut, 31, source_value)


@cocotb.test()
async def test_r5900_mtlo_source_zero_writes_zero_to_lo(dut) -> None:
    """Read architectural GPR zero and replace a nonzero primary LO with zero."""
    await initialize(dut, 0x2000)
    await execute_mtlo(dut, 0, GPR_MASK)


@cocotb.test()
async def test_r5900_mtlo_wraps_pc_and_preserves_sibling_accumulators(dut) -> None:
    """Retire at the PC boundary while HI, HI1, and LO1 hold."""
    await initialize(dut, 0xFFFF_FFFC)
    source_value = 0xAAAA_BBBB_CCCC_DDDD_8000_0000_0000_0001
    await seed_gpr(dut, 1, source_value)
    await execute_mtlo(dut, 1, source_value)
    assert int(dut.pc_o.value) == 0


@cocotb.test()
async def test_r5900_mtlo_rejects_nonzero_reserved_fields(dut) -> None:
    """Reject populated rt, rd, or sa while preserving state and PC."""
    await initialize(dut, RESERVED_TEST_PC)
    await seed_gpr(dut, 5, 0x0123_4567_89AB_CDEF)
    old_gprs = int(dut.gprs_o.value)
    old_hilo = (
        int(dut.hi_o.value),
        int(dut.lo_o.value),
        int(dut.hi1_o.value),
        int(dut.lo1_o.value),
    )
    for instruction in (
        encode_mtlo(5, reserved_rt_rd=1),
        encode_mtlo(5, reserved_rt_rd=1 << 5),
        encode_mtlo(5, reserved_rt_rd=0x3FF),
        encode_mtlo(5, reserved_sa=1),
        encode_mtlo(5, reserved_sa=31),
    ):
        dut.instruction_i.value = instruction
        dut.instruction_valid_i.value = 1
        await Timer(1, unit="ns")
        assert int(dut.execute_valid_o.value) == 0
        assert int(dut.operation_o.value) == OPERATION_NONE
        assert int(dut.execute_complete_o.value) == 0
        assert int(dut.execute_writeback_commit_o.value) == 0
        assert int(dut.execute_write_lo_valid_o.value) == 0
        assert int(dut.reserved_valid_o.value) == 1
        assert int(dut.reserved_pc_o.value) == RESERVED_TEST_PC
        assert int(dut.reserved_instruction_o.value) == instruction
        assert int(dut.gprs_o.value) == old_gprs
        assert (
            int(dut.hi_o.value),
            int(dut.lo_o.value),
            int(dut.hi1_o.value),
            int(dut.lo1_o.value),
        ) == old_hilo
        assert int(dut.pc_o.value) == RESERVED_TEST_PC
