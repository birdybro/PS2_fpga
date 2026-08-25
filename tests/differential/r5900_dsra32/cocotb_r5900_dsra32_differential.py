"""Randomized differential verification for R5900 DSRA32."""

import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from reference.ee.r5900 import GPR_COUNT, GPR_WIDTH, R5900State, encode_dsra32

OPERATION_DSRA32 = 28


async def edge(dut) -> None:
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


def pack(gprs: tuple[int, ...]) -> int:
    return sum(value << (index * GPR_WIDTH) for index, value in enumerate(gprs))


async def seed_gpr(dut, index: int, value: int) -> None:
    dut.seed_destination_i.value = index
    dut.seed_value_i.value = value
    dut.seed_commit_i.value = 1
    await edge(dut)
    dut.seed_commit_i.value = 0
    await edge(dut)


@cocotb.test()
async def test_dsra32_against_python_model(dut) -> None:
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    generator = random.Random(seed)
    dut.rst_ni.value = 0
    dut.start_pc_i.value = 0xFFFF_FF00
    dut.instruction_valid_i.value = 0
    dut.instruction_i.value = 0
    dut.seed_commit_i.value = 0
    dut.seed_destination_i.value = 0
    dut.seed_value_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1
    model = R5900State.initial(start_pc=0xFFFF_FF00)
    for index in range(1, GPR_COUNT):
        value = generator.getrandbits(GPR_WIDTH)
        await seed_gpr(dut, index, value)
        model = model.write_gpr(index, value)
    boundaries = (
        (1, 2, 0),
        (3, 4, 1),
        (5, 6, 30),
        (7, 8, 31),
        (9, 9, 13),
        (0, 10, 31),
        (31, 0, 17),
        (11, 12, 16),
        (13, 14, 8),
        (15, 16, 24),
        (17, 18, 1),
        (19, 20, 31),
    )
    random_cases = tuple(
        (generator.randrange(32), generator.randrange(32), generator.randrange(32))
        for _ in range(512)
    )
    for iteration, (destination, source, count) in enumerate((*boundaries, *random_cases)):
        instruction = encode_dsra32(destination, source, count)
        expected = model.step(instruction)
        dut.instruction_i.value = instruction
        dut.instruction_valid_i.value = 1
        await Timer(1, unit="ns")
        assert int(dut.operation_o.value) == OPERATION_DSRA32
        if destination:
            assert int(dut.execute_writeback_value_o.value) == expected.gprs[destination]
        await edge(dut)
        dut.instruction_valid_i.value = 0
        await Timer(1, unit="ns")
        assert int(dut.pc_o.value) == expected.pc, f"seed={seed} iteration={iteration}"
        assert int(dut.gprs_o.value) == pack(expected.gprs), f"seed={seed} iteration={iteration}"
        await edge(dut)
        model = expected
