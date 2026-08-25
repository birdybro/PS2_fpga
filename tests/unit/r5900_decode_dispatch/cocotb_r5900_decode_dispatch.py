"""Directed tests for R5900 legal dispatch and reserved-instruction diagnostics."""

import cocotb
from cocotb.triggers import Timer

OPERATION_NONE = 0
OPERATION_NOP = 1
OPERATION_SLL = 2
OPERATION_SRL = 3


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
async def test_r5900_decode_dispatch_reports_and_suppresses_illegal_words(dut) -> None:
    """Preserve fault PC/opcode/word while preventing execute and later writeback."""
    cases = (
        (0, 0x0000_0001),
        (4, 0x0020_0000),
        (0x0010_0000, 0x3405_1234),
        (0x8000_0180, 0x0400_0000),
        (0xFFFF_FFFC, 0xFFFF_FFFF),
    )
    for pc, instruction in cases:
        await check_dispatch(dut, (True, pc, instruction), (False, OPERATION_NONE, True))
        assert int(dut.reserved_instruction_o.value) >> 26 == instruction >> 26
