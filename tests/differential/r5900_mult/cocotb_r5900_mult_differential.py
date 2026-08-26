"""Randomized differential verification for R5900 signed word MULT."""

import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from reference.ee.r5900 import GPR_COUNT, GPR_WIDTH, R5900State, encode_mult

CLOCK_PERIOD_NS = 10
OPERATION_MULT = 35
RANDOM_CASES = 512
SCALAR_WIDTH = 64
SCALAR_MASK = (1 << SCALAR_WIDTH) - 1
WORD_WIDTH = 32
WORD_MASK = (1 << WORD_WIDTH) - 1


async def edge(dut) -> None:
    """Advance one rising edge and settle architectural state."""
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


def pack_gprs(gprs: tuple[int, ...]) -> int:
    """Pack immutable reference state using ascending architectural GPR lanes."""
    return sum(value << (index * GPR_WIDTH) for index, value in enumerate(gprs))


def signed_word(value: int) -> int:
    """Interpret the low word as a signed integer independently of the model."""
    word = value & WORD_MASK
    return word - (1 << WORD_WIDTH) if word & (1 << (WORD_WIDTH - 1)) else word


def sign_extend_word(value: int) -> int:
    """Sign-extend one product word into an unsigned 64-bit representation."""
    word = value & WORD_MASK
    return word | ((SCALAR_MASK ^ WORD_MASK) if word & (1 << 31) else 0)


def expected_product(source_a: int, source_b: int) -> tuple[int, int]:
    """Calculate independently sign-extended HI and LO product halves."""
    product = (signed_word(source_a) * signed_word(source_b)) & SCALAR_MASK
    return sign_extend_word(product >> WORD_WIDTH), sign_extend_word(product)


async def seed_gpr(dut, destination: int, value: int) -> None:
    """Initialize one nonzero GPR through the shared writeback boundary."""
    dut.seed_gpr_destination_i.value = destination
    dut.seed_gpr_value_i.value = value
    dut.seed_gpr_commit_i.value = 1
    await edge(dut)
    dut.seed_gpr_commit_i.value = 0
    await edge(dut)


async def execute_case(
    dut,
    model: R5900State,
    fields: tuple[int, int, int],
    iteration: int,
    seed: int,
) -> R5900State:
    """Execute and compare one complete differential MULT transition."""
    destination, source_a, source_b = fields
    instruction = encode_mult(destination, source_a, source_b)
    old_pc = model.pc
    old_destination = model.gprs[destination]
    expected_hi, expected_lo = expected_product(model.gprs[source_a], model.gprs[source_b])
    expected_gpr = (old_destination & ~SCALAR_MASK) | expected_lo
    expected = model.step(instruction)

    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_MULT
    assert int(dut.execute_complete_o.value) == 1
    assert int(dut.pc_advance_o.value) == 1
    assert int(dut.execute_write_hi_valid_o.value) == 1
    assert int(dut.execute_write_hi_value_o.value) == expected_hi
    assert int(dut.execute_write_lo_valid_o.value) == 1
    assert int(dut.execute_write_lo_value_o.value) == expected_lo
    assert int(dut.execute_writeback_commit_o.value) == (destination != 0)
    assert int(dut.execute_writeback_destination_o.value) == destination
    assert int(dut.execute_writeback_value_o.value) == expected_gpr
    assert int(dut.writeback_valid_o.value) == (destination != 0)
    assert int(dut.writeback_destination_o.value) == (destination if destination else 0)
    assert int(dut.writeback_value_o.value) == (expected_gpr if destination else 0)
    assert int(dut.retirement_valid_o.value) == 1
    assert int(dut.retirement_pc_o.value) == old_pc
    assert int(dut.retirement_instruction_o.value) == instruction
    assert int(dut.reserved_valid_o.value) == 0

    await edge(dut)
    dut.instruction_valid_i.value = 0
    await Timer(1, unit="ns")
    actual_pc = int(dut.pc_o.value)
    actual_gprs = int(dut.gprs_o.value)
    context = f"seed={seed} iteration={iteration} instruction=0x{instruction:08x}"
    assert actual_pc == expected.pc, (
        f"{context} expected_pc=0x{expected.pc:08x} actual_pc=0x{actual_pc:08x}"
    )
    assert actual_gprs == pack_gprs(expected.gprs), f"{context} GPR state mismatch"
    assert int(dut.hi_o.value) == expected.hi, f"{context} HI state mismatch"
    assert int(dut.lo_o.value) == expected.lo, f"{context} LO state mismatch"
    assert int(dut.hi1_o.value) == expected.hi1, f"{context} HI1 state mismatch"
    assert int(dut.lo1_o.value) == expected.lo1, f"{context} LO1 state mismatch"
    await edge(dut)
    return expected


@cocotb.test()
async def test_r5900_mult_against_python_architectural_model(dut) -> None:
    """Compare PC, GPRs, both accumulator lanes, and events over MULT cases."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    generator = random.Random(seed)
    initial_hi = generator.getrandbits(SCALAR_WIDTH)
    initial_lo = generator.getrandbits(SCALAR_WIDTH)
    initial_hi1 = generator.getrandbits(SCALAR_WIDTH)
    initial_lo1 = generator.getrandbits(SCALAR_WIDTH)

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
    for destination in range(1, GPR_COUNT):
        value = generator.getrandbits(GPR_WIDTH)
        await seed_gpr(dut, destination, value)
        model = model.write_gpr(destination, value)
    assert int(dut.gprs_o.value) == pack_gprs(model.gprs)

    boundary_cases = (
        (0, 0, 0),
        (1, 0, 2),
        (3, 4, 0),
        (5, 5, 6),
        (7, 8, 7),
        (9, 9, 9),
        (31, 1, 2),
        (1, 31, 30),
        (2, 30, 31),
        (0, 31, 31),
        (16, 17, 18),
        (30, 30, 31),
    )
    random_cases = tuple(
        (
            generator.randrange(GPR_COUNT),
            generator.randrange(GPR_COUNT),
            generator.randrange(GPR_COUNT),
        )
        for _ in range(RANDOM_CASES)
    )
    for iteration, fields in enumerate((*boundary_cases, *random_cases)):
        model = await execute_case(dut, model, fields, iteration, seed)
