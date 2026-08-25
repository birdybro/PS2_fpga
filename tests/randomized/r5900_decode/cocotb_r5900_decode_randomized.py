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
SRAV_FUNCTION = 7
LUI_OPCODE = 15
ORI_OPCODE = 13
ANDI_OPCODE = 12
XORI_OPCODE = 14
ADDIU_OPCODE = 9
ADDU_FUNCTION = 33
SUBU_FUNCTION = 35
AND_FUNCTION = 36
IMMEDIATE_OPERATIONS = {0: 2, SRL_FUNCTION: 3, SRA_FUNCTION: 4}
REGISTER_OPERATIONS = {
    SLLV_FUNCTION: 5,
    SRLV_FUNCTION: 6,
    SRAV_FUNCTION: 7,
    ADDU_FUNCTION: 13,
    SUBU_FUNCTION: 14,
    AND_FUNCTION: 15,
}


def expected_operation(word: int) -> int:
    """Model admitted immediate and register operations independently from RTL."""
    operation = 1 if word == 0 else 0
    if word != 0 and word >> 26 == 0:
        reserved_rs = (word >> 21) & 0x1F
        reserved_shift = (word >> 6) & 0x1F
        function = word & 0x3F
        if reserved_rs == 0:
            operation = IMMEDIATE_OPERATIONS.get(function, 0)
        if operation == 0 and reserved_shift == 0:
            operation = REGISTER_OPERATIONS.get(function, 0)
    elif word >> 26 == ADDIU_OPCODE:
        operation = 12
    elif word >> 26 == ANDI_OPCODE:
        operation = 10
    elif word >> 26 == XORI_OPCODE:
        operation = 11
    elif word >> 26 == ORI_OPCODE:
        operation = 9
    elif word >> 26 == LUI_OPCODE and ((word >> 21) & 0x1F) == 0:
        operation = 8
    return operation


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
        0x0000_0007,
        0x023F_F807,
        0x0000_0047,
        0x3C00_0000,
        0x3C1F_FFFF,
        0x3C20_0000,
        0x3400_0000,
        0x3421_8000,
        0x37FF_FFFF,
        0x3000_0000,
        0x3021_8000,
        0x33FF_FFFF,
        0x3800_0000,
        0x3821_8000,
        0x3BFF_FFFF,
        0x2400_0000,
        0x2421_8000,
        0x27FF_FFFF,
        0x0000_0021,
        0x023F_F821,
        0x0000_0061,
        0x0000_0023,
        0x023F_F823,
        0x0000_0063,
        0x0000_0024,
        0x023F_F824,
        0x0000_0064,
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
