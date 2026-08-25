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
async def test_r5900_decode_dispatch_sends_canonical_addu_to_execute(dut) -> None:
    """Dispatch ADDU source and destination fields without diagnostics."""
    for pc, instruction in (
        (0, 0x0000_0021),
        (4, 0x0020_0021),
        (0x0010_0000, 0x023F_F821),
    ):
        await check_dispatch(dut, (True, pc, instruction), (True, OPERATION_ADDU, False))


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
        (20, 0x3C20_0000),
        (0x0010_0000, 0x0405_1234),
        (0x8000_0180, 0x0400_0000),
        (0xFFFF_FFFC, 0xFFFF_FFFF),
    )
    for pc, instruction in cases:
        await check_dispatch(dut, (True, pc, instruction), (False, OPERATION_NONE, True))
        assert int(dut.reserved_instruction_o.value) >> 26 == instruction >> 26
