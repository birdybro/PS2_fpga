"""Randomized differential verification for R5900 LUI."""

import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from reference.ee.r5900 import GPR_COUNT, GPR_WIDTH, R5900State, encode_lui

CLOCK_PERIOD_NS = 10
OPERATION_LUI = 8
RANDOM_CASES = 512


async def edge(dut) -> None:
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


def pack_gprs(gprs: tuple[int, ...]) -> int:
    return sum(value << (index * GPR_WIDTH) for index, value in enumerate(gprs))


async def seed_gpr(dut, destination: int, value: int) -> None:
    dut.seed_destination_i.value = destination
    dut.seed_value_i.value = value
    dut.seed_commit_i.value = 1
    await edge(dut)
    dut.seed_commit_i.value = 0
    await edge(dut)


@cocotb.test()
async def test_r5900_lui_against_python_model(dut) -> None:
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

    boundaries = ((0, 0), (1, 1), (31, 0x7FFF), (7, 0x8000), (9, 0xFFFF))
    random_cases = tuple(
        (generator.randrange(GPR_COUNT), generator.randrange(1 << 16)) for _ in range(RANDOM_CASES)
    )
    for iteration, (destination, immediate) in enumerate((*boundaries, *random_cases)):
        instruction = encode_lui(destination, immediate)
        old_pc = model.pc
        expected = model.step(instruction)
        dut.instruction_i.value = instruction
        dut.instruction_valid_i.value = 1
        await Timer(1, unit="ns")
        assert int(dut.operation_o.value) == OPERATION_LUI
        assert int(dut.execute_writeback_destination_o.value) == destination
        if destination:
            assert int(dut.execute_writeback_value_o.value) == expected.gprs[destination]
        assert int(dut.retirement_pc_o.value) == old_pc
        await edge(dut)
        dut.instruction_valid_i.value = 0
        await Timer(1, unit="ns")
        assert int(dut.pc_o.value) == expected.pc, f"seed={seed} iteration={iteration}"
        assert int(dut.gprs_o.value) == pack_gprs(expected.gprs), (
            f"seed={seed} iteration={iteration} GPR state mismatch"
        )
        await edge(dut)
        model = expected
