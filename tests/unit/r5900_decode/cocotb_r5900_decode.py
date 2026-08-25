"""Directed admission tests for the initial R5900 decode skeleton."""

import cocotb
from cocotb.triggers import Timer

OPERATION_NONE = 0
OPERATION_NOP = 1


async def check_decode(dut, word: int, legal: bool, operation: int) -> None:
    """Drive one instruction and compare both admission outputs."""
    dut.instruction_i.value = word
    await Timer(1, unit="ns")
    assert int(dut.legal_o.value) == legal, f"word=0x{word:08x} legality mismatch"
    assert int(dut.operation_o.value) == operation, f"word=0x{word:08x} operation mismatch"


@cocotb.test()
async def test_r5900_decode_recognizes_only_exact_zero_word_nop(dut) -> None:
    """Admit the one exact encoding owned by the skeleton."""
    await check_decode(dut, 0x0000_0000, True, OPERATION_NOP)


@cocotb.test()
async def test_r5900_decode_rejects_every_other_primary_opcode(dut) -> None:
    """Keep all 63 non-SPECIAL primary opcode spaces closed."""
    payloads = (0, 1, 0x0155_5555, 0x02AA_AAAA, 0x03FF_FFFF)
    for opcode in range(1, 64):
        for payload in payloads:
            await check_decode(dut, (opcode << 26) | payload, False, OPERATION_NONE)


@cocotb.test()
async def test_r5900_decode_rejects_nonzero_special_encodings(dut) -> None:
    """Reject every function code and zero-function words with nonzero operands."""
    for function in range(1, 64):
        await check_decode(dut, function, False, OPERATION_NONE)

    special_field_ranges = (
        (21, 5),
        (16, 5),
        (11, 5),
        (6, 5),
    )
    for shift, width in special_field_ranges:
        mask = (1 << width) - 1
        for value in (1, 1 << (width - 1), mask):
            await check_decode(dut, value << shift, False, OPERATION_NONE)
