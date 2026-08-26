"""Randomized differential verification for R5900 signed word DIV1."""

import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from reference.ee.r5900 import GPR_COUNT, GPR_WIDTH, R5900State, encode_div1

CLOCK_PERIOD_NS = 10
OPERATION_DIV1 = 45
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
    """Pack immutable reference state using ascending architectural lanes."""
    return sum(value << (index * GPR_WIDTH) for index, value in enumerate(gprs))


def signed_word(value: int) -> int:
    """Interpret one low word independently from the Python state model."""
    word = value & WORD_MASK
    return word - (1 << WORD_WIDTH) if word & (1 << (WORD_WIDTH - 1)) else word


def expected_div1(dividend_value: int, divisor_value: int) -> tuple[int, int]:
    """Calculate the independently expected HI remainder and LO quotient."""
    dividend = signed_word(dividend_value)
    divisor = signed_word(divisor_value)
    if dividend == -(1 << 31) and divisor == -1:
        quotient, remainder = dividend, 0
    elif divisor == 0:
        quotient, remainder = (1 if dividend < 0 else -1), dividend
    else:
        magnitude = abs(dividend) // abs(divisor)
        quotient = -magnitude if (dividend < 0) != (divisor < 0) else magnitude
        remainder = dividend - quotient * divisor
    return remainder & SCALAR_MASK, quotient & SCALAR_MASK


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
    fields: tuple[int, int],
    iteration: int,
    seed: int,
) -> R5900State:
    """Execute and compare one complete differential DIV1 transition."""
    dividend_register, divisor_register = fields
    instruction = encode_div1(dividend_register, divisor_register)
    expected_hi, expected_lo = expected_div1(
        model.gprs[dividend_register], model.gprs[divisor_register]
    )
    old_pc = model.pc
    expected = model.step(instruction)

    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_DIV1
    assert int(dut.execute_complete_o.value) == 1
    assert int(dut.pc_advance_o.value) == 1
    assert int(dut.execute_write_hi_valid_o.value) == 0
    assert int(dut.execute_write_lo_valid_o.value) == 0
    assert int(dut.execute_write_hi1_valid_o.value) == 1
    assert int(dut.execute_write_hi1_value_o.value) == expected_hi
    assert int(dut.execute_write_lo1_valid_o.value) == 1
    assert int(dut.execute_write_lo1_value_o.value) == expected_lo
    assert int(dut.execute_writeback_commit_o.value) == 0
    assert int(dut.execute_writeback_destination_o.value) == 0
    assert int(dut.execute_writeback_value_o.value) == 0
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
async def test_r5900_div1_against_python_architectural_model(dut) -> None:
    """Compare PC, GPRs, both accumulator lanes, and events over DIV1 cases."""
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
    boundary_values = {
        1: 7,
        2: 3,
        3: WORD_MASK - 6,
        4: WORD_MASK - 2,
        5: 1 << 31,
        6: WORD_MASK,
        7: 0,
        8: (1 << 31) - 1,
        9: 2,
    }
    for destination in range(1, GPR_COUNT):
        value = boundary_values.get(destination, generator.getrandbits(GPR_WIDTH))
        if destination in boundary_values:
            value |= generator.getrandbits(GPR_WIDTH - WORD_WIDTH) << WORD_WIDTH
        await seed_gpr(dut, destination, value)
        model = model.write_gpr(destination, value)
    assert int(dut.gprs_o.value) == pack_gprs(model.gprs)

    boundary_cases = (
        (1, 2),
        (3, 2),
        (1, 4),
        (3, 4),
        (5, 6),
        (1, 0),
        (3, 0),
        (0, 0),
        (8, 1),
        (5, 9),
        (31, 30),
        (30, 31),
    )
    random_cases = tuple(
        (generator.randrange(GPR_COUNT), generator.randrange(GPR_COUNT))
        for _ in range(RANDOM_CASES)
    )
    for iteration, fields in enumerate((*boundary_cases, *random_cases)):
        model = await execute_case(dut, model, fields, iteration, seed)
