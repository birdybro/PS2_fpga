"""Directed tests for R5900 legal dispatch and reserved-instruction diagnostics."""

import cocotb
from cocotb.triggers import Timer

OPERATION_NONE = 0
OPERATION_NOP = 1
OPERATION_SLL = 2
OPERATION_SRL = 3
OPERATION_SRA = 4
OPERATION_SLLV = 5
OPERATION_SRLV = 6
OPERATION_SRAV = 7
OPERATION_LUI = 8
OPERATION_ORI = 9
OPERATION_ANDI = 10
OPERATION_XORI = 11
OPERATION_ADDIU = 12
OPERATION_ADDU = 13
OPERATION_SUBU = 14
OPERATION_AND = 15
OPERATION_OR = 16
OPERATION_XOR = 17
OPERATION_NOR = 18
OPERATION_SLT = 19
OPERATION_SLTU = 20
OPERATION_SLTI = 21
OPERATION_SLTIU = 22
OPERATION_DSLL = 23
OPERATION_DSRL = 24
OPERATION_DSRA = 25
OPERATION_DSLL32 = 26
OPERATION_DSRL32 = 27
OPERATION_DSRA32 = 28
OPERATION_DSLLV = 29
OPERATION_DSRLV = 30
OPERATION_DSRAV = 31
OPERATION_DADDIU = 32
OPERATION_DADDU = 33
OPERATION_DSUBU = 34
OPERATION_MULT = 35
OPERATION_MULTU = 36
OPERATION_DIV = 37
OPERATION_DIVU = 38
OPERATION_MFHI = 39
OPERATION_MFLO = 40
OPERATION_MTHI = 41


async def check_dispatch(
    dut,
    driven: tuple[bool, int, int],
    expected: tuple[bool, int, bool],
) -> None:
    """Drive one decode attempt and compare every dispatch and diagnostic field."""
    decode_valid, pc, instruction = driven
    execute_valid, operation, reserved_valid = expected
    dut.decode_valid_i.value = decode_valid
    dut.pc_i.value = pc
    dut.instruction_i.value = instruction
    await Timer(1, unit="ns")

    assert int(dut.execute_valid_o.value) == execute_valid
    assert int(dut.operation_o.value) == operation
    assert int(dut.reserved_valid_o.value) == reserved_valid
    expected_pc = pc if reserved_valid else 0
    expected_instruction = instruction if reserved_valid else 0
    assert int(dut.reserved_pc_o.value) == expected_pc
    assert int(dut.reserved_instruction_o.value) == expected_instruction


@cocotb.test()
async def test_r5900_decode_dispatch_masks_inactive_input(dut) -> None:
    """Emit neither execution nor diagnostics when no decode word is valid."""
    for pc, instruction in (
        (0, 0),
        (0x0010_0000, 0xFFFF_FFFF),
        (0xFFFF_FFFC, 0x3405_1234),
    ):
        await check_dispatch(dut, (False, pc, instruction), (False, OPERATION_NONE, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_exact_nop_to_execute(dut) -> None:
    """Dispatch the admitted NOP without producing a reserved event."""
    for pc in (0, 4, 0x0010_0000, 0xFFFF_FFFC):
        await check_dispatch(dut, (True, pc, 0), (True, OPERATION_NOP, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_sll_to_execute(dut) -> None:
    """Dispatch nonzero SLL variable fields without a reserved diagnostic."""
    for pc, instruction in (
        (0, 0x0000_0040),
        (4, 0x0001_0000),
        (0x0010_0000, 0x001F_FFC0),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_SLL, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_srl_to_execute(dut) -> None:
    """Dispatch SRL variable fields without a reserved diagnostic."""
    for pc, instruction in (
        (0, 0x0000_0002),
        (4, 0x0001_0002),
        (0x0010_0000, 0x001F_FFC2),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_SRL, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_sra_to_execute(dut) -> None:
    """Dispatch SRA variable fields without a reserved diagnostic."""
    for pc, instruction in (
        (0, 0x0000_0003),
        (4, 0x0001_0003),
        (0x0010_0000, 0x001F_FFC3),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_SRA, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_dsll_to_execute(dut) -> None:
    """Dispatch DSLL variable fields without a reserved diagnostic."""
    for pc, instruction in (
        (0, 0x0000_0038),
        (4, 0x0001_0038),
        (0x0010_0000, 0x001F_FFF8),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_DSLL, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_dsrl_to_execute(dut) -> None:
    """Dispatch DSRL variable fields without a reserved diagnostic."""
    for pc, instruction in (
        (0, 0x0000_003A),
        (4, 0x0001_003A),
        (0x0010_0000, 0x001F_FFFA),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_DSRL, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_dsra_to_execute(dut) -> None:
    """Dispatch DSRA variable fields without a reserved diagnostic."""
    for pc, instruction in (
        (0, 0x0000_003B),
        (4, 0x0001_003B),
        (0x0010_0000, 0x001F_FFFB),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_DSRA, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_dsll32_to_execute(dut) -> None:
    """Dispatch DSLL32 fields without a reserved diagnostic."""
    for pc, instruction in ((0, 0x0000_003C), (4, 0x0001_003C), (0x0010_0000, 0x001F_FFFC)):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_DSLL32, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_dsrl32_to_execute(dut) -> None:
    """Dispatch DSRL32 fields without a reserved diagnostic."""
    for pc, instruction in ((0, 0x0000_003E), (4, 0x0001_003E), (0x0010_0000, 0x001F_FFFE)):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_DSRL32, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_dsra32_to_execute(dut) -> None:
    """Dispatch DSRA32 fields without a reserved diagnostic."""
    for pc, instruction in ((0, 0x0000_003F), (4, 0x0001_003F), (0x0010_0000, 0x001F_FFFF)):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_DSRA32, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_sllv_to_execute(dut) -> None:
    """Dispatch SLLV register fields without a reserved diagnostic."""
    for pc, instruction in (
        (0, 0x0000_0004),
        (4, 0x0020_0004),
        (0x0010_0000, 0x023F_F804),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_SLLV, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_srlv_to_execute(dut) -> None:
    """Dispatch SRLV register fields without a reserved diagnostic."""
    for pc, instruction in (
        (0, 0x0000_0006),
        (4, 0x0020_0006),
        (0x0010_0000, 0x023F_F806),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_SRLV, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_srav_to_execute(dut) -> None:
    """Dispatch SRAV register fields without a reserved diagnostic."""
    for pc, instruction in (
        (0, 0x0000_0007),
        (4, 0x0020_0007),
        (0x0010_0000, 0x023F_F807),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_SRAV, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_dsllv_to_execute(dut) -> None:
    """Dispatch DSLLV register fields without a reserved diagnostic."""
    for pc, instruction in (
        (0, 0x0000_0014),
        (4, 0x0020_0014),
        (0x0010_0000, 0x023F_F814),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_DSLLV, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_dsrlv_to_execute(dut) -> None:
    """Dispatch DSRLV register fields without a reserved diagnostic."""
    for pc, instruction in (
        (0, 0x0000_0016),
        (4, 0x0020_0016),
        (0x0010_0000, 0x023F_F816),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_DSRLV, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_dsrav_to_execute(dut) -> None:
    """Dispatch DSRAV register fields without a reserved diagnostic."""
    for pc, instruction in (
        (0, 0x0000_0017),
        (4, 0x0020_0017),
        (0x0010_0000, 0x023F_F817),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_DSRAV, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_lui_to_execute(dut) -> None:
    """Dispatch LUI destination and immediate fields without a diagnostic."""
    for pc, instruction in (
        (0, 0x3C00_0000),
        (4, 0x3C01_8000),
        (0x0010_0000, 0x3C1F_FFFF),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_LUI, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_ori_to_execute(dut) -> None:
    """Dispatch ORI source, destination, and immediate fields without diagnostics."""
    for pc, instruction in (
        (0, 0x3400_0000),
        (4, 0x3421_8000),
        (0x0010_0000, 0x37FF_FFFF),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_ORI, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_andi_to_execute(dut) -> None:
    """Dispatch ANDI source, destination, and immediate fields without diagnostics."""
    for pc, instruction in (
        (0, 0x3000_0000),
        (4, 0x3021_8000),
        (0x0010_0000, 0x33FF_FFFF),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_ANDI, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_xori_to_execute(dut) -> None:
    """Dispatch XORI source, destination, and immediate fields without diagnostics."""
    for pc, instruction in (
        (0, 0x3800_0000),
        (4, 0x3821_8000),
        (0x0010_0000, 0x3BFF_FFFF),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_XORI, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_addiu_to_execute(dut) -> None:
    """Dispatch ADDIU source, destination, and immediate fields without diagnostics."""
    for pc, instruction in (
        (0, 0x2400_0000),
        (4, 0x2421_8000),
        (0x0010_0000, 0x27FF_FFFF),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_ADDIU, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_daddiu_to_execute(dut) -> None:
    """Dispatch DADDIU source, destination, and immediate fields without diagnostics."""
    for pc, instruction in (
        (0, 0x6400_0000),
        (4, 0x6421_8000),
        (0x0010_0000, 0x67FF_FFFF),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_DADDIU, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_slti_to_execute(dut) -> None:
    """Dispatch SLTI source, destination, and immediate fields without diagnostics."""
    for pc, instruction in (
        (0, 0x2800_0000),
        (4, 0x2821_8000),
        (0x0010_0000, 0x2BFF_FFFF),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_SLTI, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_sltiu_to_execute(dut) -> None:
    """Dispatch SLTIU source, destination, and immediate fields without diagnostics."""
    for pc, instruction in (
        (0, 0x2C00_0000),
        (4, 0x2C21_8000),
        (0x0010_0000, 0x2FFF_FFFF),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_SLTIU, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_addu_to_execute(dut) -> None:
    """Dispatch ADDU source and destination fields without diagnostics."""
    for pc, instruction in (
        (0, 0x0000_0021),
        (4, 0x0020_0021),
        (0x0010_0000, 0x023F_F821),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_ADDU, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_daddu_to_execute(dut) -> None:
    """Dispatch DADDU source and destination fields without diagnostics."""
    for pc, instruction in (
        (0, 0x0000_002D),
        (4, 0x0020_002D),
        (0x0010_0000, 0x023F_F82D),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_DADDU, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_dsubu_to_execute(dut) -> None:
    """Dispatch DSUBU source and destination fields without diagnostics."""
    for pc, instruction in (
        (0, 0x0000_002F),
        (4, 0x0020_002F),
        (0x0010_0000, 0x023F_F82F),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_DSUBU, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_mult_optional_destination_to_execute(dut) -> None:
    """Dispatch signed MULT with both absent and populated rd fields."""
    for pc, instruction in (
        (0, 0x0000_0018),
        (4, 0x0020_0018),
        (0x0010_0000, 0x023F_F818),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_MULT, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_multu_optional_destination_to_execute(dut) -> None:
    """Dispatch unsigned MULTU with both absent and populated rd fields."""
    for pc, instruction in (
        (0, 0x0000_0019),
        (4, 0x0020_0019),
        (0x0010_0000, 0x023F_F819),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_MULTU, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_div_to_execute(dut) -> None:
    """Dispatch signed DIV source fields while reserved fields remain clear."""
    for pc, instruction in (
        (0, 0x0000_001A),
        (4, 0x0020_001A),
        (0x0010_0000, 0x02F1_001A),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_DIV, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_divu_to_execute(dut) -> None:
    """Dispatch unsigned DIVU source fields while reserved fields remain clear."""
    for pc, instruction in (
        (0, 0x0000_001B),
        (4, 0x0020_001B),
        (0x0010_0000, 0x02F1_001B),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_DIVU, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_mfhi_to_execute(dut) -> None:
    """Dispatch every canonical MFHI destination without diagnostics."""
    for pc, instruction in (
        (0, 0x0000_0010),
        (4, 0x0000_0810),
        (0x0010_0000, 0x0000_F810),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_MFHI, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_mflo_to_execute(dut) -> None:
    """Dispatch every canonical MFLO destination without diagnostics."""
    for pc, instruction in ((0, 0x12), (4, 0x812), (0x0010_0000, 0xF812)):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_MFLO, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_mthi_to_execute(dut) -> None:
    """Dispatch every canonical MTHI source without diagnostics."""
    for pc, instruction in ((0, 0x11), (4, 0x0020_0011), (0x0010_0000, 0x03E0_0011)):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_MTHI, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_subu_to_execute(dut) -> None:
    """Dispatch SUBU source and destination fields without diagnostics."""
    for pc, instruction in (
        (0, 0x0000_0023),
        (4, 0x0020_0023),
        (0x0010_0000, 0x023F_F823),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_SUBU, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_and_to_execute(dut) -> None:
    """Dispatch AND source and destination fields without diagnostics."""
    for pc, instruction in (
        (0, 0x0000_0024),
        (4, 0x0020_0024),
        (0x0010_0000, 0x023F_F824),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_AND, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_or_to_execute(dut) -> None:
    """Dispatch OR source and destination fields without diagnostics."""
    for pc, instruction in (
        (0, 0x0000_0025),
        (4, 0x0020_0025),
        (0x0010_0000, 0x023F_F825),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_OR, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_xor_to_execute(dut) -> None:
    """Dispatch XOR source and destination fields without diagnostics."""
    for pc, instruction in (
        (0, 0x0000_0026),
        (4, 0x0020_0026),
        (0x0010_0000, 0x023F_F826),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_XOR, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_nor_to_execute(dut) -> None:
    """Dispatch NOR source and destination fields without diagnostics."""
    for pc, instruction in (
        (0, 0x0000_0027),
        (4, 0x0020_0027),
        (0x0010_0000, 0x023F_F827),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_NOR, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_slt_to_execute(dut) -> None:
    """Dispatch SLT source and destination fields without diagnostics."""
    for pc, instruction in (
        (0, 0x0000_002A),
        (4, 0x0020_002A),
        (0x0010_0000, 0x023F_F82A),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_SLT, False))


@cocotb.test()
async def test_r5900_decode_dispatch_sends_canonical_sltu_to_execute(dut) -> None:
    """Dispatch SLTU source and destination fields without diagnostics."""
    for pc, instruction in (
        (0, 0x0000_002B),
        (4, 0x0020_002B),
        (0x0010_0000, 0x023F_F82B),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_SLTU, False))


@cocotb.test()
async def test_r5900_decode_dispatch_reports_and_suppresses_illegal_words(dut) -> None:
    """Preserve fault PC/opcode/word while preventing execute and later writeback."""
    cases = (
        (0, 0x0000_0001),
        (4, 0x0020_0000),
        (8, 0x0000_0044),
        (12, 0x0000_0046),
        (16, 0x0000_0047),
        (18, 0x0000_0061),
        (19, 0x0000_0063),
        (20, 0x0000_0064),
        (21, 0x0000_0065),
        (22, 0x0000_0066),
        (23, 0x0000_0067),
        (24, 0x0000_006A),
        (25, 0x0000_006B),
        (25, 0x0000_005A),
        (25, 0x0000_081A),
        (25, 0x0000_005B),
        (25, 0x0000_081B),
        (25, 0x0020_0010),
        (25, 0x0001_0010),
        (25, 0x0000_0050),
        (25, 0x0020_0012),
        (25, 0x0001_0012),
        (25, 0x0000_0052),
        (25, 0x0001_0011),
        (25, 0x0000_0811),
        (25, 0x0000_0051),
        (26, 0x0020_0038),
        (27, 0x0020_003A),
        (28, 0x0020_003B),
        (29, 0x0020_003C),
        (30, 0x0020_003E),
        (31, 0x0020_003F),
        (32, 0x0000_0054),
        (33, 0x0000_0056),
        (34, 0x0000_0057),
        (35, 0x0000_006D),
        (36, 0x0000_006F),
        (37, 0x0000_0058),
        (38, 0x0000_0059),
        (20, 0x3C20_0000),
        (0x0010_0000, 0x0405_1234),
        (0x8000_0180, 0x0400_0000),
        (0xFFFF_FFFC, 0xFFFF_FFFF),
    )
    for pc, instruction in cases:
        await check_dispatch(dut, (True, pc, instruction), (False, OPERATION_NONE, True))
        assert int(dut.reserved_instruction_o.value) >> 26 == instruction >> 26
