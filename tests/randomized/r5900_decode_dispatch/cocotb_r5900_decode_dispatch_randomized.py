"""Deterministic randomized tests for R5900 decode dispatch diagnostics."""

import os
import random

import cocotb
from cocotb.triggers import Timer

RANDOM_CASES = 1024
SRL_FUNCTION = 2
SRA_FUNCTION = 3
SLLV_FUNCTION = 4
SRLV_FUNCTION = 6
SRAV_FUNCTION = 7
DSLL_FUNCTION = 56
DSRL_FUNCTION = 58
DSRA_FUNCTION = 59
LUI_OPCODE = 15
ORI_OPCODE = 13
ANDI_OPCODE = 12
XORI_OPCODE = 14
ADDIU_OPCODE = 9
SLTI_OPCODE = 10
SLTIU_OPCODE = 11
ADDU_FUNCTION = 33
SUBU_FUNCTION = 35
AND_FUNCTION = 36
OR_FUNCTION = 37
XOR_FUNCTION = 38
NOR_FUNCTION = 39
SLT_FUNCTION = 42
SLTU_FUNCTION = 43
IMMEDIATE_OPERATIONS = {
    0: 2,
    SRL_FUNCTION: 3,
    SRA_FUNCTION: 4,
    DSLL_FUNCTION: 23,
    DSRL_FUNCTION: 24,
    DSRA_FUNCTION: 25,
}
REGISTER_OPERATIONS = {
    SLLV_FUNCTION: 5,
    SRLV_FUNCTION: 6,
    SRAV_FUNCTION: 7,
    ADDU_FUNCTION: 13,
    SUBU_FUNCTION: 14,
    AND_FUNCTION: 15,
    OR_FUNCTION: 16,
    XOR_FUNCTION: 17,
    NOR_FUNCTION: 18,
    SLT_FUNCTION: 19,
    SLTU_FUNCTION: 20,
}


def decoded_operation(word: int) -> int:
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
    elif word >> 26 == SLTI_OPCODE:
        operation = 21
    elif word >> 26 == SLTIU_OPCODE:
        operation = 22
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
async def test_r5900_decode_dispatch_randomized(dut) -> None:
    """Compare dispatch and diagnostic mapping across seeded PC/word pairs."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    generator = random.Random(seed)
    boundary_cases = (
        (False, 0, 0),
        (True, 0, 0),
        (True, 4, 0x0000_0040),
        (True, 8, 0x001F_FFC0),
        (True, 12, 0x0000_0002),
        (True, 16, 0x001F_FFC2),
        (True, 20, 0x0000_0003),
        (True, 24, 0x001F_FFC3),
        (True, 28, 0x0000_0004),
        (True, 32, 0x023F_F804),
        (True, 36, 0x0000_0044),
        (True, 40, 0x0000_0006),
        (True, 44, 0x023F_F806),
        (True, 48, 0x0000_0046),
        (True, 52, 0x0000_0007),
        (True, 56, 0x023F_F807),
        (True, 60, 0x0000_0047),
        (True, 61, 0x0000_0038),
        (True, 62, 0x001F_FFF8),
        (True, 63, 0x0020_0038),
        (True, 64, 0x0000_003A),
        (True, 65, 0x001F_FFFA),
        (True, 66, 0x0020_003A),
        (True, 67, 0x0000_003B),
        (True, 68, 0x001F_FFFB),
        (True, 69, 0x0020_003B),
        (True, 64, 0x3C00_0000),
        (True, 68, 0x3C1F_FFFF),
        (True, 72, 0x3C20_0000),
        (True, 76, 0x3400_0000),
        (True, 80, 0x3421_8000),
        (True, 84, 0x37FF_FFFF),
        (True, 88, 0x3000_0000),
        (True, 92, 0x3021_8000),
        (True, 96, 0x33FF_FFFF),
        (True, 100, 0x3800_0000),
        (True, 104, 0x3821_8000),
        (True, 108, 0x3BFF_FFFF),
        (True, 112, 0x2400_0000),
        (True, 116, 0x2421_8000),
        (True, 120, 0x27FF_FFFF),
        (True, 121, 0x2800_0000),
        (True, 122, 0x2821_8000),
        (True, 123, 0x2BFF_FFFF),
        (True, 124, 0x2C00_0000),
        (True, 125, 0x2C21_8000),
        (True, 126, 0x2FFF_FFFF),
        (True, 124, 0x0000_0021),
        (True, 128, 0x023F_F821),
        (True, 132, 0x0000_0061),
        (True, 136, 0x0000_0023),
        (True, 140, 0x023F_F823),
        (True, 144, 0x0000_0063),
        (True, 148, 0x0000_0024),
        (True, 152, 0x023F_F824),
        (True, 156, 0x0000_0064),
        (True, 160, 0x0000_0025),
        (True, 164, 0x023F_F825),
        (True, 168, 0x0000_0065),
        (True, 172, 0x0000_0026),
        (True, 176, 0x023F_F826),
        (True, 180, 0x0000_0066),
        (True, 184, 0x0000_0027),
        (True, 188, 0x023F_F827),
        (True, 192, 0x0000_0067),
        (True, 196, 0x0000_002A),
        (True, 200, 0x023F_F82A),
        (True, 204, 0x0000_006A),
        (True, 208, 0x0000_002B),
        (True, 212, 0x023F_F82B),
        (True, 216, 0x0000_006B),
        (True, 4, 1),
        (True, 0x0010_0000, 0x0405_1234),
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

        operation = decoded_operation(instruction)
        expected_execute = decode_valid and operation != 0
        expected_reserved = decode_valid and operation == 0
        expected_operation = operation if expected_execute else 0
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
