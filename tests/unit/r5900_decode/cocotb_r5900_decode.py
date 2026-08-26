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
async def test_r5900_decode_recognizes_canonical_dsll_encodings(dut) -> None:
    """Admit DSLL fields only while the SPECIAL reserved rs field stays zero."""
    for rt, rd, shift_amount in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rt << 16) | (rd << 11) | (shift_amount << 6) | 0x38
        await check_decode(dut, word, True, OPERATION_DSLL)


@cocotb.test()
async def test_r5900_decode_recognizes_canonical_dsrl_encodings(dut) -> None:
    """Admit DSRL fields only while the SPECIAL reserved rs field stays zero."""
    for rt, rd, shift_amount in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rt << 16) | (rd << 11) | (shift_amount << 6) | 0x3A
        await check_decode(dut, word, True, OPERATION_DSRL)


@cocotb.test()
async def test_r5900_decode_recognizes_canonical_dsra_encodings(dut) -> None:
    """Admit DSRA fields only while the SPECIAL reserved rs field stays zero."""
    for rt, rd, shift_amount in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rt << 16) | (rd << 11) | (shift_amount << 6) | 0x3B
        await check_decode(dut, word, True, OPERATION_DSRA)


@cocotb.test()
async def test_r5900_decode_recognizes_canonical_dsll32_encodings(dut) -> None:
    """Admit DSLL32 fields only while reserved rs stays zero."""
    for rt, rd, shift_amount in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (31, 31, 31), (17, 9, 13)):
        word = (rt << 16) | (rd << 11) | (shift_amount << 6) | 0x3C
        await check_decode(dut, word, True, OPERATION_DSLL32)


@cocotb.test()
async def test_r5900_decode_recognizes_canonical_dsrl32_encodings(dut) -> None:
    """Admit DSRL32 fields only while reserved rs stays zero."""
    for rt, rd, shift_amount in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (31, 31, 31), (17, 9, 13)):
        word = (rt << 16) | (rd << 11) | (shift_amount << 6) | 0x3E
        await check_decode(dut, word, True, OPERATION_DSRL32)


@cocotb.test()
async def test_r5900_decode_recognizes_canonical_dsra32_encodings(dut) -> None:
    """Admit DSRA32 fields only while reserved rs stays zero."""
    for rt, rd, shift_amount in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (31, 31, 31), (17, 9, 13)):
        word = (rt << 16) | (rd << 11) | (shift_amount << 6) | 0x3F
        await check_decode(dut, word, True, OPERATION_DSRA32)


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
async def test_r5900_decode_recognizes_canonical_srav_encodings(dut) -> None:
    """Admit all SRAV register fields while its reserved shift field stays zero."""
    for rs, rt, rd in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rs << 21) | (rt << 16) | (rd << 11) | 7
        await check_decode(dut, word, True, OPERATION_SRAV)


@cocotb.test()
async def test_r5900_decode_recognizes_canonical_dsllv_encodings(dut) -> None:
    """Admit all DSLLV register fields while reserved sa stays zero."""
    for rs, rt, rd in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rs << 21) | (rt << 16) | (rd << 11) | 0x14
        await check_decode(dut, word, True, OPERATION_DSLLV)


@cocotb.test()
async def test_r5900_decode_recognizes_canonical_lui_encodings(dut) -> None:
    """Admit every LUI destination and immediate with reserved rs clear."""
    for rt, immediate in ((0, 0), (1, 0), (31, 0xFFFF), (17, 0x8000), (9, 0x1234)):
        word = (0x0F << 26) | (rt << 16) | immediate
        await check_decode(dut, word, True, OPERATION_LUI)


@cocotb.test()
async def test_r5900_decode_recognizes_every_ori_register_and_immediate_field(dut) -> None:
    """Admit ORI across the complete architectural rs and rt field ranges."""
    for rs, rt, immediate in (
        (0, 0, 0),
        (1, 0, 1),
        (0, 1, 0x7FFF),
        (31, 31, 0xFFFF),
        (17, 9, 0x8000),
    ):
        word = (0x0D << 26) | (rs << 21) | (rt << 16) | immediate
        await check_decode(dut, word, True, OPERATION_ORI)


@cocotb.test()
async def test_r5900_decode_recognizes_every_andi_register_and_immediate_field(dut) -> None:
    """Admit ANDI across the complete architectural rs and rt field ranges."""
    for rs, rt, immediate in (
        (0, 0, 0),
        (1, 0, 1),
        (0, 1, 0x7FFF),
        (31, 31, 0xFFFF),
        (17, 9, 0x8000),
    ):
        word = (0x0C << 26) | (rs << 21) | (rt << 16) | immediate
        await check_decode(dut, word, True, OPERATION_ANDI)


@cocotb.test()
async def test_r5900_decode_recognizes_every_xori_register_and_immediate_field(dut) -> None:
    """Admit XORI across the complete architectural rs and rt field ranges."""
    for rs, rt, immediate in (
        (0, 0, 0),
        (1, 0, 1),
        (0, 1, 0x7FFF),
        (31, 31, 0xFFFF),
        (17, 9, 0x8000),
    ):
        word = (0x0E << 26) | (rs << 21) | (rt << 16) | immediate
        await check_decode(dut, word, True, OPERATION_XORI)


@cocotb.test()
async def test_r5900_decode_recognizes_every_addiu_register_and_immediate_field(dut) -> None:
    """Admit ADDIU across the complete architectural rs and rt field ranges."""
    for rs, rt, immediate in (
        (0, 0, 0),
        (1, 0, 1),
        (0, 1, 0x7FFF),
        (31, 31, 0xFFFF),
        (17, 9, 0x8000),
    ):
        word = (0x09 << 26) | (rs << 21) | (rt << 16) | immediate
        await check_decode(dut, word, True, OPERATION_ADDIU)


@cocotb.test()
async def test_r5900_decode_recognizes_every_slti_register_and_immediate_field(dut) -> None:
    """Admit SLTI across the complete architectural rs and rt field ranges."""
    for rs, rt, immediate in (
        (0, 0, 0),
        (1, 0, 1),
        (0, 1, 0x7FFF),
        (31, 31, 0xFFFF),
        (17, 9, 0x8000),
    ):
        word = (0x0A << 26) | (rs << 21) | (rt << 16) | immediate
        await check_decode(dut, word, True, OPERATION_SLTI)


@cocotb.test()
async def test_r5900_decode_recognizes_every_sltiu_register_and_immediate_field(dut) -> None:
    """Admit SLTIU across the complete architectural rs and rt field ranges."""
    for rs, rt, immediate in (
        (0, 0, 0),
        (1, 0, 1),
        (0, 1, 0x7FFF),
        (31, 31, 0xFFFF),
        (17, 9, 0x8000),
    ):
        word = (0x0B << 26) | (rs << 21) | (rt << 16) | immediate
        await check_decode(dut, word, True, OPERATION_SLTIU)


@cocotb.test()
async def test_r5900_decode_recognizes_every_addu_register_field(dut) -> None:
    """Admit all ADDU register fields while its reserved shift field stays zero."""
    for rs, rt, rd in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rs << 21) | (rt << 16) | (rd << 11) | 0x21
        await check_decode(dut, word, True, OPERATION_ADDU)


@cocotb.test()
async def test_r5900_decode_recognizes_every_subu_register_field(dut) -> None:
    """Admit all SUBU register fields while its reserved shift field stays zero."""
    for rs, rt, rd in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rs << 21) | (rt << 16) | (rd << 11) | 0x23
        await check_decode(dut, word, True, OPERATION_SUBU)


@cocotb.test()
async def test_r5900_decode_recognizes_every_and_register_field(dut) -> None:
    """Admit all AND register fields while its reserved shift field stays zero."""
    for rs, rt, rd in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rs << 21) | (rt << 16) | (rd << 11) | 0x24
        await check_decode(dut, word, True, OPERATION_AND)


@cocotb.test()
async def test_r5900_decode_recognizes_every_or_register_field(dut) -> None:
    """Admit all OR register fields while its reserved shift field stays zero."""
    for rs, rt, rd in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rs << 21) | (rt << 16) | (rd << 11) | 0x25
        await check_decode(dut, word, True, OPERATION_OR)


@cocotb.test()
async def test_r5900_decode_recognizes_every_xor_register_field(dut) -> None:
    """Admit all XOR register fields while its reserved shift field stays zero."""
    for rs, rt, rd in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rs << 21) | (rt << 16) | (rd << 11) | 0x26
        await check_decode(dut, word, True, OPERATION_XOR)


@cocotb.test()
async def test_r5900_decode_recognizes_every_nor_register_field(dut) -> None:
    """Admit all NOR register fields while its reserved shift field stays zero."""
    for rs, rt, rd in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rs << 21) | (rt << 16) | (rd << 11) | 0x27
        await check_decode(dut, word, True, OPERATION_NOR)


@cocotb.test()
async def test_r5900_decode_recognizes_every_slt_register_field(dut) -> None:
    """Admit all SLT register fields while its reserved shift field stays zero."""
    for rs, rt, rd in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rs << 21) | (rt << 16) | (rd << 11) | 0x2A
        await check_decode(dut, word, True, OPERATION_SLT)


@cocotb.test()
async def test_r5900_decode_recognizes_every_sltu_register_field(dut) -> None:
    """Admit all SLTU register fields while its reserved shift field stays zero."""
    for rs, rt, rd in (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (31, 31, 31),
        (17, 9, 13),
    ):
        word = (rs << 21) | (rt << 16) | (rd << 11) | 0x2B
        await check_decode(dut, word, True, OPERATION_SLTU)


@cocotb.test()
async def test_r5900_decode_rejects_every_other_primary_opcode(dut) -> None:
    """Keep every unsupported non-SPECIAL primary opcode space closed."""
    payloads = (0, 1, 0x0155_5555, 0x02AA_AAAA, 0x03FF_FFFF)
    for opcode in (*range(1, 9), *range(16, 64)):
        for payload in payloads:
            await check_decode(dut, (opcode << 26) | payload, False, OPERATION_NONE)


@cocotb.test()
async def test_r5900_decode_rejects_unsupported_or_reserved_special_encodings(dut) -> None:
    """Reject every unsupported function and nonzero reserved SLL rs field."""
    for function in (
        *range(1, 2),
        *range(5, 6),
        *range(8, 20),
        *range(21, 33),
        *range(34, 35),
        *range(40, 42),
        *range(44, 56),
        *range(57, 58),
        *range(61, 62),
    ):
        await check_decode(dut, function, False, OPERATION_NONE)

    for value in (1, 1 << 4, 0x1F):
        await check_decode(dut, value << 21, False, OPERATION_NONE)
        await check_decode(dut, (value << 21) | 0x38, False, OPERATION_NONE)
        await check_decode(dut, (value << 21) | 0x3A, False, OPERATION_NONE)
        await check_decode(dut, (value << 21) | 0x3B, False, OPERATION_NONE)
        await check_decode(dut, (value << 21) | 0x3C, False, OPERATION_NONE)
        await check_decode(dut, (value << 21) | 0x3E, False, OPERATION_NONE)
        await check_decode(dut, (value << 21) | 0x3F, False, OPERATION_NONE)
        await check_decode(dut, (value << 6) | 4, False, OPERATION_NONE)
        await check_decode(dut, (value << 6) | 6, False, OPERATION_NONE)
        await check_decode(dut, (value << 6) | 7, False, OPERATION_NONE)
        await check_decode(dut, (value << 6) | 0x14, False, OPERATION_NONE)
        await check_decode(dut, (value << 6) | 0x21, False, OPERATION_NONE)
        await check_decode(dut, (value << 6) | 0x23, False, OPERATION_NONE)
        await check_decode(dut, (value << 6) | 0x24, False, OPERATION_NONE)
        await check_decode(dut, (value << 6) | 0x25, False, OPERATION_NONE)
        await check_decode(dut, (value << 6) | 0x26, False, OPERATION_NONE)
        await check_decode(dut, (value << 6) | 0x27, False, OPERATION_NONE)
        await check_decode(dut, (value << 6) | 0x2A, False, OPERATION_NONE)
        await check_decode(dut, (value << 6) | 0x2B, False, OPERATION_NONE)
        await check_decode(dut, (0x0F << 26) | (value << 21), False, OPERATION_NONE)
