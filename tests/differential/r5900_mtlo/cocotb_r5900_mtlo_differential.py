"""Randomized differential verification for R5900 MTLO."""

import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from reference.ee.r5900 import GPR_COUNT, GPR_WIDTH, R5900State, encode_mtlo

CLOCK_PERIOD_NS = 10
OPERATION_MTLO = 42
RANDOM_CASES = 512
SCALAR_MASK = (1 << 64) - 1


async def edge(dut) -> None:
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


def pack_gprs(gprs: tuple[int, ...]) -> int:
    return sum(value << (index * GPR_WIDTH) for index, value in enumerate(gprs))


async def seed_gpr(dut, source: int, value: int) -> None:
    dut.seed_gpr_destination_i.value = source
    dut.seed_gpr_value_i.value = value
    dut.seed_gpr_commit_i.value = 1
    await edge(dut)
    dut.seed_gpr_commit_i.value = 0
    await edge(dut)


async def execute_case(
    dut,
    model: R5900State,
    source: int,
    iteration: int,
    seed: int,
) -> R5900State:
    """Execute and compare one complete differential MTLO transition."""
    instruction = encode_mtlo(source)
    old_pc = model.pc
    expected_lo = model.read_gpr(source) & SCALAR_MASK
    expected = model.step(instruction)

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
    assert int(dut.writeback_destination_o.value) == 0
    assert int(dut.writeback_value_o.value) == 0
    assert int(dut.retirement_valid_o.value) == 1
    assert int(dut.retirement_pc_o.value) == old_pc
    assert int(dut.retirement_instruction_o.value) == instruction
    assert int(dut.reserved_valid_o.value) == 0

    await edge(dut)
    dut.instruction_valid_i.value = 0
    await Timer(1, unit="ns")
    context = f"seed={seed} iteration={iteration} instruction=0x{instruction:08x}"
    actual_pc = int(dut.pc_o.value)
    assert actual_pc == expected.pc, (
        f"{context} expected_pc=0x{expected.pc:08x} actual_pc=0x{actual_pc:08x}"
    )
    assert int(dut.gprs_o.value) == pack_gprs(expected.gprs), f"{context} GPR mismatch"
    assert int(dut.hi_o.value) == expected.hi, f"{context} HI mismatch"
    assert int(dut.lo_o.value) == expected.lo, f"{context} LO mismatch"
    assert int(dut.hi1_o.value) == expected.hi1, f"{context} HI1 mismatch"
    assert int(dut.lo1_o.value) == expected.lo1, f"{context} LO1 mismatch"
    await edge(dut)
    return expected


@cocotb.test()
async def test_r5900_mtlo_against_python_architectural_model(dut) -> None:
    """Compare all state and events over randomized 128-bit GPR values and sources."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    generator = random.Random(seed)
    initial_hi = generator.getrandbits(64)
    initial_lo = generator.getrandbits(64)
    initial_hi1 = generator.getrandbits(64)
    initial_lo1 = generator.getrandbits(64)

    dut.rst_ni.value = 0
    dut.start_pc_i.value = 0xFFFF_FF00
    dut.instruction_valid_i.value = 0
    dut.instruction_i.value = 0
    dut.seed_gpr_commit_i.value = 0
    dut.seed_gpr_destination_i.value = 0
    dut.seed_gpr_value_i.value = 0
    dut.seed_hilo_commit_i.value = 0
    dut.seed_hi_i.value = initial_hi
    dut.seed_lo_i.value = initial_lo
    dut.seed_hi1_i.value = initial_hi1
    dut.seed_lo1_i.value = initial_lo1
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1
    dut.seed_hilo_commit_i.value = 1
    await edge(dut)
    dut.seed_hilo_commit_i.value = 0

    model = R5900State.initial(
        start_pc=0xFFFF_FF00,
        hi=initial_hi,
        lo=initial_lo,
        hi1=initial_hi1,
        lo1=initial_lo1,
    )
    boundary_cases = (
        (0, (1 << GPR_WIDTH) - 1),
        (1, 1),
        (31, 0xCAFE_BABE_1234_5678_0000_0000_7FFF_FFFF),
        (1, 0xCAFE_BABE_1234_5678_0000_0000_8000_0000),
        (31, 0xCAFE_BABE_1234_5678_0000_0000_FFFF_FFFF),
        (1, 0xCAFE_BABE_1234_5678_8000_0000_0000_0000),
        (31, (1 << GPR_WIDTH) - 1),
        (0, 0x0123_4567_89AB_CDEF),
    )
    random_cases = tuple(
        (generator.randrange(GPR_COUNT), generator.getrandbits(GPR_WIDTH))
        for _ in range(RANDOM_CASES)
    )
    for iteration, (source, source_value) in enumerate((*boundary_cases, *random_cases)):
        await seed_gpr(dut, source, source_value)
        model = model.write_gpr(source, source_value)
        model = await execute_case(dut, model, source, iteration, seed)
