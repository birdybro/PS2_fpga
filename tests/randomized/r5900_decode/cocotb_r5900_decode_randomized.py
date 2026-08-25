"""Deterministic randomized admission tests for the R5900 decode skeleton."""

import os
import random

import cocotb
from cocotb.triggers import Timer

RANDOM_CASES = 2048
SRL_FUNCTION = 2
SRA_FUNCTION = 3
SLLV_FUNCTION = 4
SRLV_FUNCTION = 6


def expected_operation(word: int) -> int:
    """Model admitted constant and variable shifts independently from the RTL."""
    if word == 0:
        return 1
    opcode = word >> 26
    reserved_rs = (word >> 21) & 0x1F
    reserved_shift = (word >> 6) & 0x1F
    function = word & 0x3F
    if opcode == 0 and reserved_rs == 0 and function == 0:
        return 2
    if opcode == 0 and reserved_rs == 0 and function == SRL_FUNCTION:
        return 3
    if opcode == 0 and reserved_rs == 0 and function == SRA_FUNCTION:
        return 4
    if opcode == 0 and reserved_shift == 0 and function == SLLV_FUNCTION:
        return 5
    return 6 if opcode == 0 and reserved_shift == 0 and function == SRLV_FUNCTION else 0


@cocotb.test()
async def test_r5900_decode_randomized_admission(dut) -> None:
    """Require implemented shift recognition over reproducible arbitrary words."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    generator = random.Random(seed)
    boundary_words = (
        0,
        1,
        0x0000_0040,
        0x0000_0002,
        0x001F_FFC2,
        0x0000_0003,
        0x001F_FFC3,
        0x0000_0004,
        0x023F_F804,
        0x0000_0044,
        0x0000_0006,
        0x023F_F806,
        0x0000_0046,
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
