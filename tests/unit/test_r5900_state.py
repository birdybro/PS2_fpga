"""Directed boundary tests for timing-free R5900 architectural state."""

from dataclasses import FrozenInstanceError

import pytest

from reference.ee.r5900 import GPR_COUNT, GPR_MASK, PC_MASK, R5900State

EE_PROGRAM_START = 0x0010_0000
PRESERVED_GPR_VALUE = 0x55
PC_COPY_START = 0x1000


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
