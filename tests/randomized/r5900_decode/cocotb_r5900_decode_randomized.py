"""Deterministic randomized admission tests for the R5900 decode skeleton."""

import os
import random

import cocotb
from cocotb.triggers import Timer

RANDOM_CASES = 2048


def expected_operation(word: int) -> int:
    """Model the admitted NOP/SLL encodings independently from the RTL decoder."""
    if word == 0:
        return 1
    opcode = word >> 26
    reserved_rs = (word >> 21) & 0x1F
    function = word & 0x3F
    return 2 if opcode == 0 and reserved_rs == 0 and function == 0 else 0


@cocotb.test()
async def test_r5900_decode_randomized_admission(dut) -> None:
    """Require NOP/SLL recognition over reproducible arbitrary encodings."""
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
        operation = expected_operation(word)
        expected_legal = operation != 0
        actual_legal = int(dut.legal_o.value)
        actual_operation = int(dut.operation_o.value)
        assert (actual_legal, actual_operation) == (expected_legal, operation), (
            f"seed={seed} iteration={iteration} word=0x{word:08x} "
            f"expected=({expected_legal}, {operation}) "
            f"actual=({actual_legal}, {actual_operation})"
        )
