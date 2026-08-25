"""Directed admission tests for the initial R5900 decode skeleton."""

import cocotb
from cocotb.triggers import Timer

OPERATION_NONE = 0
OPERATION_NOP = 1
OPERATION_SLL = 2
OPERATION_SRL = 3
OPERATION_SRA = 4
OPERATION_SLLV = 5
OPERATION_SRLV = 6


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
async def test_r5900_decode_recognizes_canonical_nonzero_sll_encodings(dut) -> None:
    """Admit every variable field while keeping the SPECIAL reserved field zero."""
    for rt, rd, shift_amount in (
        (0, 0, 1),
        (1, 0, 0),
        (0, 1, 0),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rt << 16) | (rd << 11) | (shift_amount << 6)
        await check_decode(dut, word, True, OPERATION_SLL)


@cocotb.test()
async def test_r5900_decode_recognizes_canonical_srl_encodings(dut) -> None:
    """Admit SRL variable fields while the SPECIAL reserved field remains zero."""
    for rt, rd, shift_amount in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rt << 16) | (rd << 11) | (shift_amount << 6) | 2
        await check_decode(dut, word, True, OPERATION_SRL)


@cocotb.test()
async def test_r5900_decode_recognizes_canonical_sra_encodings(dut) -> None:
    """Admit SRA variable fields while the SPECIAL reserved field remains zero."""
    for rt, rd, shift_amount in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rt << 16) | (rd << 11) | (shift_amount << 6) | 3
        await check_decode(dut, word, True, OPERATION_SRA)


@cocotb.test()
async def test_r5900_decode_recognizes_canonical_sllv_encodings(dut) -> None:
    """Admit all SLLV register fields while its reserved shift field stays zero."""
    for rs, rt, rd in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rs << 21) | (rt << 16) | (rd << 11) | 4
        await check_decode(dut, word, True, OPERATION_SLLV)


@cocotb.test()
async def test_r5900_decode_recognizes_canonical_srlv_encodings(dut) -> None:
    """Admit all SRLV register fields while its reserved shift field stays zero."""
    for rs, rt, rd in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rs << 21) | (rt << 16) | (rd << 11) | 6
        await check_decode(dut, word, True, OPERATION_SRLV)


@cocotb.test()
async def test_r5900_decode_rejects_every_other_primary_opcode(dut) -> None:
    """Keep all 63 non-SPECIAL primary opcode spaces closed."""
    payloads = (0, 1, 0x0155_5555, 0x02AA_AAAA, 0x03FF_FFFF)
    for opcode in range(1, 64):
        for payload in payloads:
            await check_decode(dut, (opcode << 26) | payload, False, OPERATION_NONE)


@cocotb.test()
async def test_r5900_decode_rejects_unsupported_or_reserved_special_encodings(dut) -> None:
    """Reject every unsupported function and nonzero reserved SLL rs field."""
    for function in (*range(1, 2), *range(5, 6), *range(7, 64)):
        await check_decode(dut, function, False, OPERATION_NONE)

    for value in (1, 1 << 4, 0x1F):
        await check_decode(dut, value << 21, False, OPERATION_NONE)
        await check_decode(dut, (value << 6) | 4, False, OPERATION_NONE)
        await check_decode(dut, (value << 6) | 6, False, OPERATION_NONE)
