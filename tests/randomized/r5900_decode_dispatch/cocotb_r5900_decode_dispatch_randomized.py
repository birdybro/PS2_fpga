"""Deterministic randomized tests for R5900 decode dispatch diagnostics."""

import os
import random

import cocotb
from cocotb.triggers import Timer

RANDOM_CASES = 1024


@cocotb.test()
async def test_r5900_decode_dispatch_randomized(dut) -> None:
    """Compare dispatch and diagnostic mapping across seeded PC/word pairs."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    generator = random.Random(seed)
    boundary_cases = (
        (False, 0, 0),
        (True, 0, 0),
        (True, 4, 1),
        (True, 0x0010_0000, 0x3405_1234),
        (True, 0xFFFF_FFFC, 0xFFFF_FFFF),
    )
    random_cases = tuple(
        (
            bool(generator.getrandbits(1)),
            generator.getrandbits(32),
            generator.getrandbits(32),
        )
        for _ in range(RANDOM_CASES)
    )

    for iteration, (decode_valid, pc, instruction) in enumerate((*boundary_cases, *random_cases)):
        dut.decode_valid_i.value = decode_valid
        dut.pc_i.value = pc
        dut.instruction_i.value = instruction
        await Timer(1, unit="ns")

        expected_execute = decode_valid and instruction == 0
        expected_reserved = decode_valid and instruction != 0
        expected_operation = 1 if expected_execute else 0
        expected_pc = pc if expected_reserved else 0
        expected_instruction = instruction if expected_reserved else 0
        actual = (
            int(dut.execute_valid_o.value),
            int(dut.operation_o.value),
            int(dut.reserved_valid_o.value),
            int(dut.reserved_pc_o.value),
            int(dut.reserved_instruction_o.value),
        )
        expected = (
            expected_execute,
            expected_operation,
            expected_reserved,
            expected_pc,
            expected_instruction,
        )
        assert actual == expected, (
            f"seed={seed} iteration={iteration} pc=0x{pc:08x} "
            f"instruction=0x{instruction:08x} expected={expected} actual={actual}"
        )
