"""Randomized differential verification for exact zero-word R5900 NOP."""

import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from reference.ee.r5900 import GPR_COUNT, GPR_WIDTH, R5900State

CLOCK_PERIOD_NS = 10
RANDOM_STATES = 256


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


@cocotb.test()
async def test_r5900_nop_against_python_architectural_model(dut) -> None:
    """Compare PC, all GPRs, writeback, and retirement over seeded states."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    generator = random.Random(seed)
    dut.rst_ni.value = 0
    dut.start_pc_i.value = 0
    dut.instruction_valid_i.value = 0
    dut.instruction_i.value = 0
    dut.seed_commit_i.value = 0
    dut.seed_destination_i.value = 0
    dut.seed_value_i.value = 0
    dut.read_index_a_i.value = 0
    dut.read_index_b_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1

    model = R5900State.initial()
    for destination in range(1, GPR_COUNT):
        value = generator.getrandbits(GPR_WIDTH)
        await seed_gpr(dut, destination, value)
        model = model.write_gpr(destination, value)
    expected_gprs = pack_gprs(model.gprs)
    assert int(dut.gprs_o.value) == expected_gprs

    boundary_pcs = (0, 4, 0x0010_0000, 0xFFFF_FFFC)
    random_pcs = tuple(generator.getrandbits(30) << 2 for _ in range(RANDOM_STATES))
    for iteration, start_pc in enumerate((*boundary_pcs, *random_pcs)):
        dut.instruction_valid_i.value = 0
        dut.start_pc_i.value = start_pc
        dut.rst_ni.value = 0
        await edge(dut)
        dut.rst_ni.value = 1
        model = R5900State(gprs=model.gprs, pc=start_pc)

        dut.instruction_i.value = 0
        dut.instruction_valid_i.value = 1
        await Timer(1, unit="ns")
        assert int(dut.execute_complete_o.value) == 1
        assert int(dut.retirement_valid_o.value) == 1
        assert int(dut.retirement_pc_o.value) == model.pc
        assert int(dut.retirement_instruction_o.value) == 0
        assert int(dut.execute_writeback_commit_o.value) == 0
        assert int(dut.writeback_valid_o.value) == 0

        expected = model.step(0)
        await edge(dut)
        dut.instruction_valid_i.value = 0
        await Timer(1, unit="ns")
        actual_pc = int(dut.pc_o.value)
        actual_gprs = int(dut.gprs_o.value)
        assert actual_pc == expected.pc, (
            f"seed={seed} iteration={iteration} start_pc=0x{start_pc:08x} "
            f"expected_pc=0x{expected.pc:08x} actual_pc=0x{actual_pc:08x}"
        )
        assert actual_gprs == pack_gprs(expected.gprs), (
            f"seed={seed} iteration={iteration} GPR state changed during NOP"
        )
        model = expected
