"""Randomized differential verification for R5900 DSRLV."""

import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from reference.ee.r5900 import GPR_COUNT, GPR_WIDTH, R5900State, encode_dsrlv

OPERATION_DSRLV = 30


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
async def test_dsrlv_against_python_model(dut) -> None:
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
    controlled_values = {
        1: 0,
        2: 1,
        3: 31,
        4: 32,
        5: 63,
        6: 64,
        7: (1 << GPR_WIDTH) - 1,
        10: 0xDEAD_BEEF_CAFE_F00D_FEDC_BA98_7654_3210,
    }
    for index, value in controlled_values.items():
        await seed_gpr(dut, index, value)
        model = model.write_gpr(index, value)
    boundaries = (
        (20, 10, 1),
        (21, 10, 2),
        (22, 10, 3),
        (23, 10, 4),
        (24, 10, 5),
        (25, 10, 6),
        (0, 10, 7),
        (10, 10, 2),
        (8, 8, 8),
        (9, 9, 9),
        (11, 12, 11),
        (13, 14, 15),
    )
    random_cases = tuple(
        (
            generator.randrange(GPR_COUNT),
            generator.randrange(GPR_COUNT),
            generator.randrange(GPR_COUNT),
        )
        for _ in range(512)
    )
    for iteration, (destination, source, shift_register) in enumerate((*boundaries, *random_cases)):
        instruction = encode_dsrlv(destination, source, shift_register)
        expected = model.step(instruction)
        dut.instruction_i.value = instruction
        dut.instruction_valid_i.value = 1
        await Timer(1, unit="ns")
        assert int(dut.operation_o.value) == OPERATION_DSRLV
        assert int(dut.source_rs_value_o.value) == model.gprs[shift_register]
        if destination:
            assert int(dut.execute_writeback_value_o.value) == expected.gprs[destination]
        await edge(dut)
        dut.instruction_valid_i.value = 0
        await Timer(1, unit="ns")
        assert int(dut.pc_o.value) == expected.pc, f"seed={seed} iteration={iteration}"
        assert int(dut.gprs_o.value) == pack(expected.gprs), f"seed={seed} iteration={iteration}"
        await edge(dut)
        model = expected
