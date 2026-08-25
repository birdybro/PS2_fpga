"""Deterministic randomized admission tests for the R5900 decode skeleton."""

import os
import random

import cocotb
from cocotb.triggers import Timer

RANDOM_CASES = 2048


@cocotb.test()
async def test_r5900_decode_randomized_exact_nop_admission(dut) -> None:
    """Require exact zero-word recognition over reproducible arbitrary encodings."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    generator = random.Random(seed)
    boundary_words = (
        0,
        1,
        0x0000_0040,
        0x0000_0800,
        0x0001_0000,
        0x0020_0000,
        0x03FF_FFFF,
        0x0400_0000,
        0x7FFF_FFFF,
        0x8000_0000,
        0xFFFF_FFFF,
    )
    words = (*boundary_words, *(generator.getrandbits(32) for _ in range(RANDOM_CASES)))

    for iteration, word in enumerate(words):
        dut.instruction_i.value = word
        await Timer(1, unit="ns")
        expected_legal = word == 0
        expected_operation = 1 if expected_legal else 0
        actual_legal = int(dut.legal_o.value)
        actual_operation = int(dut.operation_o.value)
        assert (actual_legal, actual_operation) == (expected_legal, expected_operation), (
            f"seed={seed} iteration={iteration} word=0x{word:08x} "
            f"expected=({expected_legal}, {expected_operation}) "
            f"actual=({actual_legal}, {actual_operation})"
        )
