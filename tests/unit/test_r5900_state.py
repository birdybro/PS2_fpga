"""Directed boundary tests for timing-free R5900 architectural state."""

from dataclasses import FrozenInstanceError

import pytest

from reference.ee.r5900 import (
    GPR_COUNT,
    GPR_MASK,
    PC_MASK,
    R5900State,
    UnsupportedInstructionError,
    encode_andi,
    encode_lui,
    encode_ori,
    encode_sll,
    encode_sllv,
    encode_sra,
    encode_srav,
    encode_srl,
    encode_srlv,
    encode_xori,
)

EE_PROGRAM_START = 0x0010_0000
PRESERVED_GPR_VALUE = 0x55
PC_COPY_START = 0x1000
ALIASED_SLL_RESULT = 0xCAFE_BABE_1234_5678_FFFF_FFFF_8000_0010
TWO_INSTRUCTION_PC = 8
ONE_INSTRUCTION_PC = 4
ALIASED_SRL_RESULT = 0xCAFE_BABE_1234_5678_0000_0000_0800_0001
ALIASED_SRA_RESULT = 0xCAFE_BABE_1234_5678_FFFF_FFFF_F800_0001
ALIASED_SLLV_RESULT = 0xCAFE_BABE_1234_5678_FFFF_FFFF_8000_0010
ALIASED_SLLV_RS_RESULT = 0x0123_4567_89AB_CDEF_FFFF_FFFF_8000_0000
ALIASED_SRLV_RESULT = 0xCAFE_BABE_1234_5678_0000_0000_0800_0001
ALIASED_SRLV_RS_RESULT = 0x0123_4567_89AB_CDEF_0000_0000_4000_0000
ALIASED_SRAV_RESULT = 0xCAFE_BABE_1234_5678_FFFF_FFFF_F800_0001
ALIASED_SRAV_RS_RESULT = 0x0123_4567_89AB_CDEF_FFFF_FFFF_C000_0000
ENCODED_LUI_EXAMPLE = 0x3C1F_1234
ENCODED_ORI_EXAMPLE = 0x36FF_1234
ENCODED_ANDI_EXAMPLE = 0x32FF_1234
ENCODED_XORI_EXAMPLE = 0x3AFF_1234


@pytest.mark.unit
@pytest.mark.parametrize("start_pc", [0, 1, PC_MASK])
def test_r5900_initial_state_has_exact_widths(start_pc: int) -> None:
    """Create all 32 128-bit zero GPRs at every PC boundary class."""
    state = R5900State.initial(start_pc=start_pc)

    assert len(state.gprs) == GPR_COUNT
    assert state.gprs == (0,) * GPR_COUNT
    assert state.pc == start_pc


@pytest.mark.unit
@pytest.mark.parametrize("start_pc", [-1, PC_MASK + 1, True])
def test_r5900_initial_state_rejects_invalid_start_pc(start_pc: object) -> None:
    """Do not truncate a loader-provided entry point or accept Boolean coercion."""
    expected = TypeError if type(start_pc) is bool else ValueError
    with pytest.raises(expected):
        R5900State.initial(start_pc=start_pc)  # type: ignore[arg-type]


@pytest.mark.unit
def test_r5900_state_is_immutable_and_updates_by_copy() -> None:
    """Keep earlier snapshots stable while independently changing every writable GPR."""
    initial = R5900State.initial(start_pc=EE_PROGRAM_START)
    state = initial
    expected = [0] * GPR_COUNT
    for index in range(1, GPR_COUNT):
        value = ((1 << 127) | (index << 64) | index) & GPR_MASK
        state = state.write_gpr(index, value)
        expected[index] = value

    assert initial.gprs == (0,) * GPR_COUNT
    assert initial.pc == EE_PROGRAM_START
    assert state.gprs == tuple(expected)
    assert state.pc == initial.pc
    with pytest.raises(FrozenInstanceError):
        state.pc = 4  # type: ignore[misc]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 0),
        (GPR_MASK, GPR_MASK),
        (1 << 128, 0),
        ((1 << 132) | 0xA5, 0xA5),
        (-1, GPR_MASK),
    ],
)
def test_r5900_gpr_results_are_explicitly_128_bit(value: int, expected: int) -> None:
    """Normalize unlimited Python integers exactly at the architectural write boundary."""
    assert R5900State.initial().write_gpr(31, value).read_gpr(31) == expected


@pytest.mark.unit
def test_r5900_register_zero_ignores_full_width_writes() -> None:
    """Preserve all 128 zero bits for boundary and overflowing write values."""
    state = R5900State.initial().write_gpr(7, PRESERVED_GPR_VALUE)
    for value in (0, 1, GPR_MASK, 1 << 128, -1):
        updated = state.write_gpr(0, value)
        assert updated is state
        assert updated.read_gpr(0) == 0
        assert updated.read_gpr(7) == PRESERVED_GPR_VALUE


@pytest.mark.unit
@pytest.mark.parametrize("index", [-1, GPR_COUNT, True])
def test_r5900_gpr_access_rejects_invalid_indices(index: object) -> None:
    """Reject out-of-range and implicitly coerced register selectors."""
    state = R5900State.initial()
    expected = TypeError if type(index) is bool else IndexError
    with pytest.raises(expected):
        state.read_gpr(index)  # type: ignore[arg-type]
    with pytest.raises(expected):
        state.write_gpr(index, 0)  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.parametrize("value", [True, 1.0, "1"])
def test_r5900_computed_writes_reject_non_integer_values(value: object) -> None:
    """Reject Python coercions that could conceal a reference-model width defect."""
    state = R5900State.initial()
    with pytest.raises(TypeError):
        state.write_gpr(1, value)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        state.write_pc(value)  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.parametrize(
    "gprs",
    [
        [0] * GPR_COUNT,
        (0,) * (GPR_COUNT - 1),
        (0,) * (GPR_COUNT + 1),
        (1,) + (0,) * (GPR_COUNT - 1),
        (0,) * (GPR_COUNT - 1) + (-1,),
        (0,) * (GPR_COUNT - 1) + (GPR_MASK + 1,),
    ],
)
def test_r5900_snapshot_rejects_malformed_gpr_state(gprs: object) -> None:
    """Prevent mutable, incorrectly sized, nonzero-zero, or out-of-width snapshots."""
    expected = TypeError if isinstance(gprs, list) else ValueError
    with pytest.raises(expected):
        R5900State(gprs=gprs)  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, 0), (PC_MASK, PC_MASK), (1 << 32, 0), ((1 << 36) | 0x40, 0x40), (-1, PC_MASK)],
)
def test_r5900_computed_pc_is_explicitly_32_bit(value: int, expected: int) -> None:
    """Normalize future sequential and redirected PC calculations at one boundary."""
    initial = R5900State.initial(start_pc=PC_COPY_START)
    updated = initial.write_pc(value)

    assert updated.pc == expected
    assert updated.gprs == initial.gprs
    if expected != initial.pc:
        assert initial.pc == PC_COPY_START


@pytest.mark.unit
def test_r5900_reference_nop_preserves_gprs_and_advances_pc() -> None:
    """Model exact zero-word NOP as only a modulo-32-bit four-byte PC advance."""
    seeded = R5900State.initial()
    for index in range(1, GPR_COUNT):
        seeded = seeded.write_gpr(index, (index << 120) | (1 << index) | index)

    boundaries = ((0, 4), (4, 8), (0x0010_0000, 0x0010_0004), (PC_MASK - 3, 0))
    for start_pc, expected_pc in boundaries:
        state = R5900State(gprs=seeded.gprs, pc=start_pc)
        updated = state.step(0)
        assert updated.pc == expected_pc
        assert updated.gprs == state.gprs
        assert state.pc == start_pc


@pytest.mark.unit
@pytest.mark.parametrize(
    ("shift_amount", "low_word", "expected_scalar"),
    [
        (0, 0x7FFF_FFFF, 0x0000_0000_7FFF_FFFF),
        (0, 0x8000_0000, 0xFFFF_FFFF_8000_0000),
        (1, 0x4000_0000, 0xFFFF_FFFF_8000_0000),
        (30, 0x0000_0003, 0xFFFF_FFFF_C000_0000),
        (31, 0x0000_0001, 0xFFFF_FFFF_8000_0000),
    ],
)
def test_r5900_reference_sll_word_and_destination_width_rules(
    shift_amount: int,
    low_word: int,
    expected_scalar: int,
) -> None:
    """Shift only rt low word, sign-extend to 64 bits, and preserve rd upper 64."""
    source = 0xDEAD_BEEF_CAFE_F00D_1234_5678_0000_0000 | low_word
    old_destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
    state = R5900State.initial(start_pc=PC_MASK - 3)
    state = state.write_gpr(3, source).write_gpr(5, old_destination)

    updated = state.step(encode_sll(5, 3, shift_amount))

    assert updated.read_gpr(5) == (old_destination & ~((1 << 64) - 1)) | expected_scalar
    assert updated.read_gpr(3) == source
    assert updated.pc == 0


@pytest.mark.unit
def test_r5900_reference_sll_reads_before_aliased_write_and_protects_zero() -> None:
    """Handle rd equal to rt and legal non-NOP writes targeting GPR zero."""
    original = 0xCAFE_BABE_1234_5678_8765_4321_0800_0001
    state = R5900State.initial().write_gpr(7, original)
    aliased = state.step(encode_sll(7, 7, 4))
    assert aliased.read_gpr(7) == ALIASED_SLL_RESULT

    discarded = aliased.step(encode_sll(0, 7, 31))
    assert discarded.read_gpr(0) == 0
    assert discarded.read_gpr(7) == aliased.read_gpr(7)
    assert discarded.pc == TWO_INSTRUCTION_PC


@pytest.mark.unit
@pytest.mark.parametrize(
    ("destination", "source", "shift_amount", "error"),
    [
        (-1, 0, 0, IndexError),
        (GPR_COUNT, 0, 0, IndexError),
        (0, -1, 0, IndexError),
        (0, GPR_COUNT, 0, IndexError),
        (0, 0, -1, ValueError),
        (0, 0, 32, ValueError),
        (True, 0, 0, TypeError),
        (0, 0, True, TypeError),
    ],
)
def test_r5900_sll_encoder_rejects_non_fields(
    destination: object,
    source: object,
    shift_amount: object,
    error: type[Exception],
) -> None:
    """Reject values that cannot occupy canonical SLL register and shift fields."""
    with pytest.raises(error):
        encode_sll(destination, source, shift_amount)  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("shift_amount", "low_word", "expected_scalar"),
    [
        (0, 0x7FFF_FFFF, 0x0000_0000_7FFF_FFFF),
        (0, 0xF000_0001, 0xFFFF_FFFF_F000_0001),
        (1, 0xF000_0000, 0x0000_0000_7800_0000),
        (30, 0xF000_0000, 0x0000_0000_0000_0003),
        (31, 0x8000_0000, 0x0000_0000_0000_0001),
    ],
)
def test_r5900_reference_srl_word_and_destination_width_rules(
    shift_amount: int,
    low_word: int,
    expected_scalar: int,
) -> None:
    """Logically shift rt low word, then apply the EE scalar destination rule."""
    source = 0xDEAD_BEEF_CAFE_F00D_1234_5678_0000_0000 | low_word
    old_destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
    state = R5900State.initial(start_pc=PC_MASK - 3)
    state = state.write_gpr(3, source).write_gpr(5, old_destination)

    updated = state.step(encode_srl(5, 3, shift_amount))

    assert updated.read_gpr(5) == (old_destination & ~((1 << 64) - 1)) | expected_scalar
    assert updated.read_gpr(3) == source
    assert updated.pc == 0


@pytest.mark.unit
def test_r5900_reference_srl_reads_before_alias_and_protects_zero() -> None:
    """Handle rd equal to rt and legal SRL writes targeting GPR zero."""
    original = 0xCAFE_BABE_1234_5678_8765_4321_8000_0010
    state = R5900State.initial().write_gpr(7, original)
    aliased = state.step(encode_srl(7, 7, 4))
    assert aliased.read_gpr(7) == ALIASED_SRL_RESULT

    discarded = aliased.step(encode_srl(0, 7, 31))
    assert discarded.read_gpr(0) == 0
    assert discarded.read_gpr(7) == aliased.read_gpr(7)
    assert discarded.pc == TWO_INSTRUCTION_PC


@pytest.mark.unit
def test_r5900_srl_encoder_sets_function_and_variable_fields() -> None:
    """Place canonical SRL variable fields without changing reserved rs."""
    assert encode_srl(31, 17, 31) == (17 << 16) | (31 << 11) | (31 << 6) | 2


@pytest.mark.unit
@pytest.mark.parametrize(
    ("shift_amount", "low_word", "expected_scalar"),
    [
        (0, 0x7FFF_FFFF, 0x0000_0000_7FFF_FFFF),
        (0, 0x8000_0000, 0xFFFF_FFFF_8000_0000),
        (1, 0x8000_0000, 0xFFFF_FFFF_C000_0000),
        (30, 0x8000_0000, 0xFFFF_FFFF_FFFF_FFFE),
        (31, 0x8000_0000, 0xFFFF_FFFF_FFFF_FFFF),
        (31, 0x7FFF_FFFF, 0x0000_0000_0000_0000),
    ],
)
def test_r5900_reference_sra_word_and_destination_width_rules(
    shift_amount: int,
    low_word: int,
    expected_scalar: int,
) -> None:
    """Arithmetically shift rt low word and preserve the destination upper lane."""
    source = 0xDEAD_BEEF_CAFE_F00D_1234_5678_0000_0000 | low_word
    old_destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
    state = R5900State.initial(start_pc=PC_MASK - 3)
    state = state.write_gpr(3, source).write_gpr(5, old_destination)

    updated = state.step(encode_sra(5, 3, shift_amount))

    assert updated.read_gpr(5) == (old_destination & ~((1 << 64) - 1)) | expected_scalar
    assert updated.read_gpr(3) == source
    assert updated.pc == 0


@pytest.mark.unit
def test_r5900_reference_sra_reads_before_alias_and_protects_zero() -> None:
    """Handle rd equal to rt and legal SRA writes targeting GPR zero."""
    original = 0xCAFE_BABE_1234_5678_8765_4321_8000_0010
    state = R5900State.initial().write_gpr(7, original)
    aliased = state.step(encode_sra(7, 7, 4))
    assert aliased.read_gpr(7) == ALIASED_SRA_RESULT

    discarded = aliased.step(encode_sra(0, 7, 31))
    assert discarded.read_gpr(0) == 0
    assert discarded.read_gpr(7) == aliased.read_gpr(7)
    assert discarded.pc == TWO_INSTRUCTION_PC


@pytest.mark.unit
def test_r5900_sra_encoder_sets_function_and_variable_fields() -> None:
    """Place canonical SRA variable fields without changing reserved rs."""
    assert encode_sra(31, 17, 31) == (17 << 16) | (31 << 11) | (31 << 6) | 3


@pytest.mark.unit
@pytest.mark.parametrize(
    ("shift_register_value", "low_word", "expected_scalar"),
    [
        (0, 0x7FFF_FFFF, 0x0000_0000_7FFF_FFFF),
        (0, 0x8000_0000, 0xFFFF_FFFF_8000_0000),
        (1, 0x4000_0000, 0xFFFF_FFFF_8000_0000),
        (31, 0x0000_0001, 0xFFFF_FFFF_8000_0000),
        (32, 0x7FFF_FFFF, 0x0000_0000_7FFF_FFFF),
        (33, 0x4000_0000, 0xFFFF_FFFF_8000_0000),
        (0xFFFF_FFFF, 0x0000_0001, 0xFFFF_FFFF_8000_0000),
    ],
)
def test_r5900_reference_sllv_masks_count_and_merges_destination(
    shift_register_value: int,
    low_word: int,
    expected_scalar: int,
) -> None:
    """Use rs low five bits, shift rt low word, and retain rd upper 64 bits."""
    shift_register = 0xF00D_CAFE_1234_5678_9ABC_DEF0_0000_0000 | shift_register_value
    source = 0xDEAD_BEEF_CAFE_F00D_1234_5678_0000_0000 | low_word
    old_destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
    state = R5900State.initial(start_pc=PC_MASK - 3)
    state = state.write_gpr(2, shift_register)
    state = state.write_gpr(3, source).write_gpr(5, old_destination)

    updated = state.step(encode_sllv(5, 3, 2))

    assert updated.read_gpr(5) == (old_destination & ~((1 << 64) - 1)) | expected_scalar
    assert updated.read_gpr(2) == shift_register
    assert updated.read_gpr(3) == source
    assert updated.pc == 0


@pytest.mark.unit
def test_r5900_reference_sllv_reads_all_operands_before_alias_write() -> None:
    """Preserve original rt, rs, and rd values for aliased variable shifts."""
    original = 0xCAFE_BABE_1234_5678_8765_4321_0800_0001
    state = R5900State.initial().write_gpr(2, 4).write_gpr(7, original)
    rd_equals_rt = state.step(encode_sllv(7, 7, 2))
    assert rd_equals_rt.read_gpr(7) == ALIASED_SLLV_RESULT

    count_and_destination = 0x0123_4567_89AB_CDEF_1111_2222_0000_0021
    state = rd_equals_rt.write_gpr(8, 0x4000_0000).write_gpr(9, count_and_destination)
    rd_equals_rs = state.step(encode_sllv(9, 8, 9))
    assert rd_equals_rs.read_gpr(9) == ALIASED_SLLV_RS_RESULT


@pytest.mark.unit
def test_r5900_reference_sllv_protects_zero_and_encodes_reserved_sa() -> None:
    """Suppress destination zero and leave the encoded shift field clear."""
    state = R5900State.initial().write_gpr(2, 31).write_gpr(3, 1)
    discarded = state.step(encode_sllv(0, 3, 2))
    assert discarded.read_gpr(0) == 0
    assert discarded.gprs[1:] == state.gprs[1:]
    assert discarded.pc == ONE_INSTRUCTION_PC
    assert encode_sllv(31, 17, 9) == (9 << 21) | (17 << 16) | (31 << 11) | 4


@pytest.mark.unit
@pytest.mark.parametrize(
    ("shift_register_value", "low_word", "expected_scalar"),
    [
        (0, 0x8000_0001, 0xFFFF_FFFF_8000_0001),
        (1, 0x8000_0001, 0x0000_0000_4000_0000),
        (31, 0x8000_0001, 0x0000_0000_0000_0001),
        (32, 0x8000_0001, 0xFFFF_FFFF_8000_0001),
        (33, 0x8000_0001, 0x0000_0000_4000_0000),
        (0xFFFF_FFFF, 0x8000_0001, 0x0000_0000_0000_0001),
        (30, 0xF000_0000, 0x0000_0000_0000_0003),
    ],
)
def test_r5900_reference_srlv_masks_count_and_merges_destination(
    shift_register_value: int,
    low_word: int,
    expected_scalar: int,
) -> None:
    """Use rs low five bits for a logical rt word shift and retain rd upper bits."""
    shift_register = 0xF00D_CAFE_1234_5678_9ABC_DEF0_0000_0000 | shift_register_value
    source = 0xDEAD_BEEF_CAFE_F00D_1234_5678_0000_0000 | low_word
    old_destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
    state = R5900State.initial(start_pc=PC_MASK - 3)
    state = state.write_gpr(2, shift_register)
    state = state.write_gpr(3, source).write_gpr(5, old_destination)

    updated = state.step(encode_srlv(5, 3, 2))

    assert updated.read_gpr(5) == (old_destination & ~((1 << 64) - 1)) | expected_scalar
    assert updated.read_gpr(2) == shift_register
    assert updated.read_gpr(3) == source
    assert updated.pc == 0


@pytest.mark.unit
def test_r5900_reference_srlv_reads_all_operands_before_alias_write() -> None:
    """Preserve original rt, rs, and rd values for aliased variable shifts."""
    original = 0xCAFE_BABE_1234_5678_8765_4321_8000_0010
    state = R5900State.initial().write_gpr(2, 4).write_gpr(7, original)
    rd_equals_rt = state.step(encode_srlv(7, 7, 2))
    assert rd_equals_rt.read_gpr(7) == ALIASED_SRLV_RESULT

    count_and_destination = 0x0123_4567_89AB_CDEF_1111_2222_0000_0021
    state = rd_equals_rt.write_gpr(8, 0x8000_0000).write_gpr(9, count_and_destination)
    rd_equals_rs = state.step(encode_srlv(9, 8, 9))
    assert rd_equals_rs.read_gpr(9) == ALIASED_SRLV_RS_RESULT


@pytest.mark.unit
def test_r5900_reference_srlv_protects_zero_and_encodes_reserved_sa() -> None:
    """Suppress destination zero and leave the encoded shift field clear."""
    state = R5900State.initial().write_gpr(2, 31).write_gpr(3, 0x8000_0001)
    discarded = state.step(encode_srlv(0, 3, 2))
    assert discarded.read_gpr(0) == 0
    assert discarded.gprs[1:] == state.gprs[1:]
    assert discarded.pc == ONE_INSTRUCTION_PC
    assert encode_srlv(31, 17, 9) == (9 << 21) | (17 << 16) | (31 << 11) | 6


@pytest.mark.unit
@pytest.mark.parametrize(
    ("shift_register_value", "low_word", "expected_scalar"),
    [
        (0, 0x8000_0001, 0xFFFF_FFFF_8000_0001),
        (1, 0x8000_0001, 0xFFFF_FFFF_C000_0000),
        (30, 0x8000_0000, 0xFFFF_FFFF_FFFF_FFFE),
        (31, 0x8000_0001, 0xFFFF_FFFF_FFFF_FFFF),
        (31, 0x7FFF_FFFF, 0x0000_0000_0000_0000),
        (32, 0x8000_0001, 0xFFFF_FFFF_8000_0001),
        (33, 0x8000_0001, 0xFFFF_FFFF_C000_0000),
        (0xFFFF_FFFF, 0x8000_0001, 0xFFFF_FFFF_FFFF_FFFF),
    ],
)
def test_r5900_reference_srav_masks_count_and_merges_destination(
    shift_register_value: int,
    low_word: int,
    expected_scalar: int,
) -> None:
    """Use rs low five bits for an arithmetic rt shift and retain rd upper bits."""
    shift_register = 0xF00D_CAFE_1234_5678_9ABC_DEF0_0000_0000 | shift_register_value
    source = 0xDEAD_BEEF_CAFE_F00D_1234_5678_0000_0000 | low_word
    old_destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
    state = R5900State.initial(start_pc=PC_MASK - 3)
    state = state.write_gpr(2, shift_register)
    state = state.write_gpr(3, source).write_gpr(5, old_destination)

    updated = state.step(encode_srav(5, 3, 2))

    assert updated.read_gpr(5) == (old_destination & ~((1 << 64) - 1)) | expected_scalar
    assert updated.read_gpr(2) == shift_register
    assert updated.read_gpr(3) == source
    assert updated.pc == 0


@pytest.mark.unit
def test_r5900_reference_srav_reads_all_operands_before_alias_write() -> None:
    """Preserve original rt, rs, and rd values for aliased variable shifts."""
    original = 0xCAFE_BABE_1234_5678_8765_4321_8000_0010
    state = R5900State.initial().write_gpr(2, 4).write_gpr(7, original)
    rd_equals_rt = state.step(encode_srav(7, 7, 2))
    assert rd_equals_rt.read_gpr(7) == ALIASED_SRAV_RESULT

    count_and_destination = 0x0123_4567_89AB_CDEF_1111_2222_0000_0021
    state = rd_equals_rt.write_gpr(8, 0x8000_0000).write_gpr(9, count_and_destination)
    rd_equals_rs = state.step(encode_srav(9, 8, 9))
    assert rd_equals_rs.read_gpr(9) == ALIASED_SRAV_RS_RESULT


@pytest.mark.unit
def test_r5900_reference_srav_protects_zero_and_encodes_reserved_sa() -> None:
    """Suppress destination zero and leave the encoded shift field clear."""
    state = R5900State.initial().write_gpr(2, 31).write_gpr(3, 0x8000_0001)
    discarded = state.step(encode_srav(0, 3, 2))
    assert discarded.read_gpr(0) == 0
    assert discarded.gprs[1:] == state.gprs[1:]
    assert discarded.pc == ONE_INSTRUCTION_PC
    assert encode_srav(31, 17, 9) == (9 << 21) | (17 << 16) | (31 << 11) | 7


@pytest.mark.unit
@pytest.mark.parametrize(
    ("immediate", "expected_scalar"),
    [
        (0x0000, 0x0000_0000_0000_0000),
        (0x0001, 0x0000_0000_0001_0000),
        (0x7FFF, 0x0000_0000_7FFF_0000),
        (0x8000, 0xFFFF_FFFF_8000_0000),
        (0xFFFF, 0xFFFF_FFFF_FFFF_0000),
    ],
)
def test_r5900_reference_lui_forms_signed_word_and_preserves_upper_lane(
    immediate: int,
    expected_scalar: int,
) -> None:
    """Place the immediate in word bits 31:16 and retain destination bits 127:64."""
    old_destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
    state = R5900State.initial(start_pc=PC_MASK - 3).write_gpr(5, old_destination)

    updated = state.step(encode_lui(5, immediate))

    assert updated.read_gpr(5) == (old_destination & ~((1 << 64) - 1)) | expected_scalar
    assert updated.pc == 0


@pytest.mark.unit
def test_r5900_reference_lui_protects_zero_and_validates_encoding() -> None:
    """Suppress LUI to GPR zero and reject values outside the immediate field."""
    state = R5900State.initial().write_gpr(3, 0x55)
    discarded = state.step(encode_lui(0, 0xFFFF))
    assert discarded.gprs == state.gprs
    assert discarded.pc == ONE_INSTRUCTION_PC
    assert encode_lui(31, 0x1234) == ENCODED_LUI_EXAMPLE
    for immediate in (-1, 0x1_0000, True):
        error = TypeError if type(immediate) is bool else ValueError
        with pytest.raises(error):
            encode_lui(1, immediate)  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.parametrize("immediate", [0, 1, 0x7FFF, 0x8000, 0xFFFF])
def test_r5900_reference_ori_zero_extends_and_preserves_destination_upper_lane(
    immediate: int,
) -> None:
    """OR the unsigned immediate into rs bits 63:0 and preserve rt bits 127:64."""
    source = 0xFFFF_FFFF_FFFF_FFFF_1234_5678_9ABC_0000
    destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
    state = R5900State.initial(start_pc=PC_MASK - 3)
    state = state.write_gpr(4, source).write_gpr(5, destination)

    updated = state.step(encode_ori(5, 4, immediate))

    expected_scalar = (source & ((1 << 64) - 1)) | immediate
    expected = (destination & ~((1 << 64) - 1)) | expected_scalar
    assert updated.read_gpr(5) == expected
    assert updated.read_gpr(4) == source
    assert updated.pc == 0


@pytest.mark.unit
def test_r5900_reference_ori_handles_aliases_zero_and_encoder_validation() -> None:
    """Cover source aliasing, the hardwired zero destination, and exact encoding."""
    aliased = 0xCAFE_BABE_1234_5678_FEDC_BA98_7654_0000
    state = R5900State.initial().write_gpr(31, aliased)
    updated = state.step(encode_ori(31, 31, 0xFFFF))
    assert updated.read_gpr(31) == aliased | 0xFFFF
    discarded = updated.step(encode_ori(0, 31, 0x1234))
    assert discarded.gprs == updated.gprs
    assert discarded.pc == TWO_INSTRUCTION_PC
    assert encode_ori(31, 23, 0x1234) == ENCODED_ORI_EXAMPLE
    for immediate in (-1, 0x1_0000, True):
        error = TypeError if type(immediate) is bool else ValueError
        with pytest.raises(error):
            encode_ori(1, 2, immediate)  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.parametrize("immediate", [0, 1, 0x7FFF, 0x8000, 0xFFFF])
def test_r5900_reference_andi_zero_extends_and_preserves_destination_upper_lane(
    immediate: int,
) -> None:
    """AND rs bits 63:0 with the unsigned immediate and preserve rt bits 127:64."""
    source = 0xFFFF_FFFF_FFFF_FFFF_FEDC_BA98_7654_F0F0
    destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
    state = R5900State.initial(start_pc=PC_MASK - 3)
    state = state.write_gpr(4, source).write_gpr(5, destination)

    updated = state.step(encode_andi(5, 4, immediate))

    expected = (destination & ~((1 << 64) - 1)) | ((source & 0xFFFF) & immediate)
    assert updated.read_gpr(5) == expected
    assert updated.read_gpr(4) == source
    assert updated.pc == 0


@pytest.mark.unit
def test_r5900_reference_andi_handles_aliases_zero_and_encoder_validation() -> None:
    """Cover source aliasing, both zero roles, and exact ANDI encoding."""
    aliased = 0xCAFE_BABE_1234_5678_FEDC_BA98_7654_F0F0
    state = R5900State.initial().write_gpr(31, aliased)
    updated = state.step(encode_andi(31, 31, 0x0FF0))
    assert updated.read_gpr(31) == (aliased & ~((1 << 64) - 1)) | 0x00F0
    discarded = updated.step(encode_andi(0, 31, 0xFFFF))
    assert discarded.gprs == updated.gprs
    assert discarded.pc == TWO_INSTRUCTION_PC
    zero_source = discarded.step(encode_andi(31, 0, 0xFFFF))
    assert zero_source.read_gpr(31) == aliased & ~((1 << 64) - 1)
    assert encode_andi(31, 23, 0x1234) == ENCODED_ANDI_EXAMPLE
    for immediate in (-1, 0x1_0000, True):
        error = TypeError if type(immediate) is bool else ValueError
        with pytest.raises(error):
            encode_andi(1, 2, immediate)  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.parametrize("immediate", [0, 1, 0x7FFF, 0x8000, 0xFFFF])
def test_r5900_reference_xori_zero_extends_and_preserves_destination_upper_lane(
    immediate: int,
) -> None:
    """XOR rs bits 63:0 with the unsigned immediate and preserve rt bits 127:64."""
    source = 0xFFFF_FFFF_FFFF_FFFF_FEDC_BA98_7654_F0F0
    destination = 0x0123_4567_89AB_CDEF_AAAA_BBBB_CCCC_DDDD
    state = R5900State.initial(start_pc=PC_MASK - 3)
    state = state.write_gpr(4, source).write_gpr(5, destination)

    updated = state.step(encode_xori(5, 4, immediate))

    expected = (destination & ~((1 << 64) - 1)) | ((source & ((1 << 64) - 1)) ^ immediate)
    assert updated.read_gpr(5) == expected
    assert updated.read_gpr(4) == source
    assert updated.pc == 0


@pytest.mark.unit
def test_r5900_reference_xori_handles_aliases_zero_and_encoder_validation() -> None:
    """Cover source aliasing, both zero roles, and exact XORI encoding."""
    aliased = 0xCAFE_BABE_1234_5678_FEDC_BA98_7654_F0F0
    state = R5900State.initial().write_gpr(31, aliased)
    updated = state.step(encode_xori(31, 31, 0xFFFF))
    assert updated.read_gpr(31) == aliased ^ 0xFFFF
    discarded = updated.step(encode_xori(0, 31, 0x1234))
    assert discarded.gprs == updated.gprs
    assert discarded.pc == TWO_INSTRUCTION_PC
    zero_source = discarded.step(encode_xori(31, 0, 0x8000))
    assert zero_source.read_gpr(31) == (aliased & ~((1 << 64) - 1)) | 0x8000
    assert encode_xori(31, 23, 0x1234) == ENCODED_XORI_EXAMPLE
    for immediate in (-1, 0x1_0000, True):
        error = TypeError if type(immediate) is bool else ValueError
        with pytest.raises(error):
            encode_xori(1, 2, immediate)  # type: ignore[arg-type]


@pytest.mark.unit
def test_r5900_reference_step_rejects_unsupported_and_invalid_words() -> None:
    """Keep unimplemented encodings and malformed instruction inputs outside the model."""
    state = R5900State.initial()
    for instruction in (1, 0x0020_0000, 0x0405_1234, PC_MASK):
        with pytest.raises(UnsupportedInstructionError):
            state.step(instruction)
    for instruction, error in ((-1, ValueError), (PC_MASK + 1, ValueError), (True, TypeError)):
        with pytest.raises(error):
            state.step(instruction)  # type: ignore[arg-type]
