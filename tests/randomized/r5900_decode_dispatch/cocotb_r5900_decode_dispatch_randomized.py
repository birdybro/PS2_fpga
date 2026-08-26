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
DSLLV_FUNCTION = 20
DSRLV_FUNCTION = 22
DSRAV_FUNCTION = 23
DSLL_FUNCTION = 56
DSRL_FUNCTION = 58
DSRA_FUNCTION = 59
DSLL32_FUNCTION = 60
DSRL32_FUNCTION = 62
DSRA32_FUNCTION = 63
LUI_OPCODE = 15
ORI_OPCODE = 13
ANDI_OPCODE = 12
XORI_OPCODE = 14
ADDIU_OPCODE = 9
DADDIU_OPCODE = 25
SLTI_OPCODE = 10
SLTIU_OPCODE = 11
MMI_OPCODE = 28
ADDU_FUNCTION = 33
DADDU_FUNCTION = 45
DSUBU_FUNCTION = 47
MULT_FUNCTION = 24
MULTU_FUNCTION = 25
DIV_FUNCTION = 26
DIVU_FUNCTION = 27
MFHI_FUNCTION = 16
MTHI_FUNCTION = 17
MFLO_FUNCTION = 18
MTLO_FUNCTION = 19
MULT1_FUNCTION = 24
MULTU1_FUNCTION = 25
DIV1_FUNCTION = 26
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
    DSLL32_FUNCTION: 26,
    DSRL32_FUNCTION: 27,
    DSRA32_FUNCTION: 28,
}
REGISTER_OPERATIONS = {
    SLLV_FUNCTION: 5,
    SRLV_FUNCTION: 6,
    SRAV_FUNCTION: 7,
    DSLLV_FUNCTION: 29,
    DSRLV_FUNCTION: 30,
    DSRAV_FUNCTION: 31,
    ADDU_FUNCTION: 13,
    DADDU_FUNCTION: 33,
    DSUBU_FUNCTION: 34,
    MULT_FUNCTION: 35,
    MULTU_FUNCTION: 36,
    SUBU_FUNCTION: 14,
    AND_FUNCTION: 15,
    OR_FUNCTION: 16,
    XOR_FUNCTION: 17,
    NOR_FUNCTION: 18,
    SLT_FUNCTION: 19,
    SLTU_FUNCTION: 20,
}


def decoded_special_operation(word: int) -> int:
    """Model one nonzero SPECIAL word with its overlapping reserved fields."""
    reserved_rs = (word >> 21) & 0x1F
    reserved_shift = (word >> 6) & 0x1F
    function = word & 0x3F
    operation = IMMEDIATE_OPERATIONS.get(function, 0) if reserved_rs == 0 else 0
    if function == DIV_FUNCTION and ((word >> 6) & 0x3FF) == 0:
        operation = 37
    if function == DIVU_FUNCTION and ((word >> 6) & 0x3FF) == 0:
        operation = 38
    if function in (MFHI_FUNCTION, MFLO_FUNCTION) and (word & 0x03FF_07C0) == 0:
        operation = 39 if function == MFHI_FUNCTION else 40
    if function == MTHI_FUNCTION and (word & 0x001F_FFC0) == 0:
        operation = 41
    if function == MTLO_FUNCTION and (word & 0x001F_FFC0) == 0:
        operation = 42
    if operation == 0 and reserved_shift == 0:
        operation = REGISTER_OPERATIONS.get(function, 0)
    return operation


def decoded_operation(word: int) -> int:
    """Model admitted immediate and register operations independently from RTL."""
    operation = 1 if word == 0 else 0
    if word != 0 and word >> 26 == 0:
        operation = decoded_special_operation(word)
    elif word >> 26 == ADDIU_OPCODE:
        operation = 12
    elif word >> 26 == DADDIU_OPCODE:
        operation = 32
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
    elif word >> 26 == MMI_OPCODE:
        function = word & 0x3F
        if ((word >> 6) & 0x1F) == 0:
            mmi_operations = {MULT1_FUNCTION: 43, MULTU1_FUNCTION: 44}
            operation = mmi_operations.get(function, 0)
        if (word & 0xFFC0) == 0 and function == DIV1_FUNCTION:
            operation = 45
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
        (True, 70, 0x0000_003C),
        (True, 71, 0x001F_FFFC),
        (True, 72, 0x0020_003C),
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
        (True, 120, 0x6400_0000),
        (True, 121, 0x6421_8000),
        (True, 122, 0x67FF_FFFF),
        (True, 121, 0x2800_0000),
        (True, 122, 0x2821_8000),
        (True, 123, 0x2BFF_FFFF),
        (True, 124, 0x2C00_0000),
        (True, 125, 0x2C21_8000),
        (True, 126, 0x2FFF_FFFF),
        (True, 124, 0x0000_0021),
        (True, 128, 0x023F_F821),
        (True, 129, 0x0000_002D),
        (True, 130, 0x023F_F82D),
        (True, 131, 0x0000_006D),
        (True, 132, 0x0000_002F),
        (True, 133, 0x023F_F82F),
        (True, 134, 0x0000_006F),
        (True, 135, 0x0000_0018),
        (True, 136, 0x023F_F818),
        (True, 137, 0x0000_0058),
        (True, 138, 0x0000_0019),
        (True, 139, 0x023F_F819),
        (True, 140, 0x0000_0059),
        (True, 141, 0x0000_001A),
        (True, 142, 0x03FF_001A),
        (True, 143, 0x0000_005A),
        (True, 144, 0x0000_081A),
        (True, 145, 0x0000_001B),
        (True, 146, 0x03FF_001B),
        (True, 147, 0x0000_005B),
        (True, 148, 0x0000_081B),
        (True, 149, 0x0000_0010),
        (True, 150, 0x0000_F810),
        (True, 151, 0x0020_0010),
        (True, 152, 0x0001_0010),
        (True, 153, 0x0000_0050),
        (True, 154, 0x0000_0012),
        (True, 155, 0x0000_F812),
        (True, 156, 0x0020_0012),
        (True, 157, 0x0001_0012),
        (True, 158, 0x0000_0052),
        (True, 159, 0x0000_0011),
        (True, 160, 0x03E0_0011),
        (True, 161, 0x0001_0011),
        (True, 162, 0x0000_0811),
        (True, 163, 0x0000_0051),
        (True, 164, 0x0000_0013),
        (True, 165, 0x03E0_0013),
        (True, 166, 0x0001_0013),
        (True, 167, 0x0000_0813),
        (True, 168, 0x0000_0053),
        (True, 169, 0x7000_0018),
        (True, 170, 0x72FF_F818),
        (True, 171, 0x7000_0058),
        (True, 172, 0x7000_0019),
        (True, 173, 0x72FF_F819),
        (True, 174, 0x7000_0059),
        (True, 175, 0x7000_001A),
        (True, 176, 0x73FF_001A),
        (True, 177, 0x7000_005A),
        (True, 178, 0x7000_081A),
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
