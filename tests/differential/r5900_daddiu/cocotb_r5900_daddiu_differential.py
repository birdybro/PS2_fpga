"""Randomized differential verification for R5900 DADDIU."""

import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from reference.ee.r5900 import (
    GPR_COUNT,
    GPR_MASK,
    GPR_WIDTH,
    SCALAR_MASK,
    R5900State,
    encode_daddiu,
)

CLOCK_PERIOD_NS = 10
OPERATION_DADDIU = 32
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
async def test_r5900_daddiu_against_python_model(dut) -> None:
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

    boundaries = (
        (0, 0, 0),
        (1, 0, 1),
        (31, 31, 0xFFFF),
        (7, 7, 0x8000),
        (9, 3, 0x7FFF),
        (3, 9, 0x0000),
        (5, 31, 0x8001),
        (31, 5, 0xFFFE),
        (4, 4, 0x0001),
        (8, 8, 0xFFFF),
        (12, 0, 0x8000),
        (0, 12, 0x7FFF),
    )
    random_cases = tuple(
        (
            generator.randrange(GPR_COUNT),
            generator.randrange(GPR_COUNT),
            generator.randrange(1 << 16),
        )
        for _ in range(RANDOM_CASES)
    )
    for iteration, (destination, source, immediate) in enumerate((*boundaries, *random_cases)):
        instruction = encode_daddiu(destination, source, immediate)
        old_pc = model.pc
        signed_immediate = immediate - (1 << 16) if immediate & 0x8000 else immediate
        result_scalar = ((model.gprs[source] & SCALAR_MASK) + signed_immediate) & SCALAR_MASK
        expected_candidate = (model.gprs[destination] & (GPR_MASK ^ SCALAR_MASK)) | result_scalar
        expected = model.step(instruction)
        dut.instruction_i.value = instruction
        dut.instruction_valid_i.value = 1
        await Timer(1, unit="ns")
        assert int(dut.operation_o.value) == OPERATION_DADDIU
        assert int(dut.execute_writeback_destination_o.value) == destination
        assert int(dut.execute_writeback_value_o.value) == expected_candidate
        assert int(dut.retirement_pc_o.value) == old_pc
        assert int(dut.retirement_instruction_o.value) == instruction
        await edge(dut)
        dut.instruction_valid_i.value = 0
        await Timer(1, unit="ns")
        assert int(dut.pc_o.value) == expected.pc, f"seed={seed} iteration={iteration}"
        assert int(dut.gprs_o.value) == pack_gprs(expected.gprs), (
            f"seed={seed} iteration={iteration} GPR state mismatch"
        )
        await edge(dut)
        model = expected
