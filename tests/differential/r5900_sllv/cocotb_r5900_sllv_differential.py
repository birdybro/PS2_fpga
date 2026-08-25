"""Randomized differential verification for R5900 32-bit SLLV."""

import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from reference.ee.r5900 import GPR_COUNT, GPR_WIDTH, R5900State, encode_sllv

CLOCK_PERIOD_NS = 10
OPERATION_SLLV = 5
RANDOM_CASES = 512


async def edge(dut) -> None:
    """Advance one rising edge and settle architectural state."""
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


def pack_gprs(gprs: tuple[int, ...]) -> int:
    """Pack immutable reference state using ascending architectural GPR lanes."""
    return sum(value << (index * GPR_WIDTH) for index, value in enumerate(gprs))


async def seed_gpr(dut, destination: int, value: int) -> None:
    """Initialize one nonzero GPR through the shared writeback boundary."""
    dut.seed_destination_i.value = destination
    dut.seed_value_i.value = value
    dut.seed_commit_i.value = 1
    await edge(dut)
    dut.seed_commit_i.value = 0
    await edge(dut)


async def execute_case(
    dut,
    model: R5900State,
    fields: tuple[int, int, int],
    iteration: int,
    seed: int,
) -> R5900State:
    """Execute and compare one complete differential SLLV transition."""
    destination, source, shift_register = fields
    instruction = encode_sllv(destination, source, shift_register)
    old_pc = model.pc
    expected = model.step(instruction)

    dut.instruction_i.value = instruction
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == OPERATION_SLLV
    assert int(dut.execute_complete_o.value) == 1
    assert int(dut.pc_advance_o.value) == 1
    assert int(dut.source_rs_value_o.value) == model.gprs[shift_register]
    assert int(dut.source_rt_value_o.value) == model.gprs[source]
    assert int(dut.execute_writeback_commit_o.value) == 1
    assert int(dut.execute_writeback_destination_o.value) == destination
    assert int(dut.commit_accepted_o.value) == 1
    if destination:
        assert int(dut.execute_writeback_value_o.value) == expected.gprs[destination]
    assert int(dut.writeback_valid_o.value) == (destination != 0)
    assert int(dut.writeback_destination_o.value) == (destination if destination else 0)
    assert int(dut.writeback_value_o.value) == (expected.gprs[destination] if destination else 0)
    assert int(dut.retirement_valid_o.value) == 1
    assert int(dut.retirement_pc_o.value) == old_pc
    assert int(dut.retirement_instruction_o.value) == instruction
    assert int(dut.reserved_valid_o.value) == 0

    await edge(dut)
    dut.instruction_valid_i.value = 0
    await Timer(1, unit="ns")
    actual_pc = int(dut.pc_o.value)
    actual_gprs = int(dut.gprs_o.value)
    assert actual_pc == expected.pc, (
        f"seed={seed} iteration={iteration} instruction=0x{instruction:08x} "
        f"expected_pc=0x{expected.pc:08x} actual_pc=0x{actual_pc:08x}"
    )
    assert actual_gprs == pack_gprs(expected.gprs), (
        f"seed={seed} iteration={iteration} instruction=0x{instruction:08x} "
        "architectural GPR state mismatch"
    )
    await edge(dut)
    return expected


@cocotb.test()
async def test_r5900_sllv_against_python_architectural_model(dut) -> None:
    """Compare all state and events over boundary and seeded SLLV cases."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    generator = random.Random(seed)
    dut.rst_ni.value = 0
    dut.start_pc_i.value = 0xFFFF_FF00
    dut.instruction_valid_i.value = 0
    dut.instruction_i.value = 0
    dut.seed_commit_i.value = 0
    dut.seed_destination_i.value = 0
    dut.seed_value_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1

    model = R5900State.initial(start_pc=0xFFFF_FF00)
    for destination in range(1, GPR_COUNT):
        value = generator.getrandbits(GPR_WIDTH)
        await seed_gpr(dut, destination, value)
        model = model.write_gpr(destination, value)

    controlled_values = {
        1: 0,
        2: 1,
        3: 31,
        4: 32,
        5: 33,
        6: (1 << GPR_WIDTH) - 1,
        10: 0xDEAD_BEEF_CAFE_F00D_1234_5678_8000_0001,
    }
    for destination, value in controlled_values.items():
        await seed_gpr(dut, destination, value)
        model = model.write_gpr(destination, value)
    assert int(dut.gprs_o.value) == pack_gprs(model.gprs)

    boundary_cases = (
        (20, 10, 1),
        (21, 10, 2),
        (22, 10, 3),
        (23, 10, 4),
        (24, 10, 5),
        (0, 10, 6),
        (10, 10, 2),
        (7, 10, 7),
        (8, 8, 8),
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
