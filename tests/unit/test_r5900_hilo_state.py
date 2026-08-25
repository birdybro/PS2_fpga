"""Directed boundary tests for timing-free R5900 HI/LO architectural state."""

from dataclasses import FrozenInstanceError

import pytest

from reference.ee.r5900 import GPR_COUNT, HILO_MASK, R5900State

HILO_FIELDS = ("hi", "lo", "hi1", "lo1")
PROGRAM_START = 0x0010_0000
GPR_SENTINEL = 0xAA
EXPECTED_NOP_PC = 16
INITIAL_VALUES = {
    "hi": 0x0123_4567_89AB_CDEF,
    "lo": 0xFEDC_BA98_7654_3210,
    "hi1": 0x8000_0000_0000_0000,
    "lo1": HILO_MASK,
}


def write_hilo(state: R5900State, field_name: str, value: int) -> R5900State:
    """Call one explicitly named HI/LO successor boundary."""
    return getattr(state, f"write_{field_name}")(value)


@pytest.mark.unit
def test_r5900_initial_state_accepts_explicit_independent_hilo_values() -> None:
    """Initialize all four 64-bit registers without coupling either pipeline."""
    state = R5900State.initial(start_pc=PROGRAM_START, **INITIAL_VALUES)

    assert state.pc == PROGRAM_START
    assert state.gprs == (0,) * GPR_COUNT
    for field_name, expected in INITIAL_VALUES.items():
        assert getattr(state, field_name) == expected


@pytest.mark.unit
@pytest.mark.parametrize("field_name", HILO_FIELDS)
def test_r5900_hilo_initial_and_snapshot_values_require_exact_width(field_name: str) -> None:
    """Reject overflow, negative, and Boolean state rather than repairing snapshots."""
    for value, error in ((-1, ValueError), (HILO_MASK + 1, ValueError), (True, TypeError)):
        fields = {field_name: value}
        with pytest.raises(error):
            R5900State.initial(**fields)  # type: ignore[arg-type]
        with pytest.raises(error):
            R5900State(**fields)  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.parametrize("field_name", HILO_FIELDS)
def test_r5900_computed_hilo_writes_normalize_to_64_bits(field_name: str) -> None:
    """Mask unlimited Python integers only at a computed-result boundary."""
    initial = R5900State.initial(**INITIAL_VALUES)
    cases = ((0, 0), (HILO_MASK, HILO_MASK), (1 << 64, 0), (-1, HILO_MASK))
    for value, expected in cases:
        updated = write_hilo(initial, field_name, value)
        assert getattr(updated, field_name) == expected
        for other_name in HILO_FIELDS:
            if other_name != field_name:
                assert getattr(updated, other_name) == getattr(initial, other_name)


@pytest.mark.unit
def test_r5900_hilo_updates_are_immutable_independent_successors() -> None:
    """Keep earlier snapshots stable while updating each pair independently."""
    initial = R5900State.initial()
    with_hi = initial.write_hi(1)
    with_lo = with_hi.write_lo(2)
    with_hi1 = with_lo.write_hi1(3)
    complete = with_hi1.write_lo1(4)

    assert (initial.hi, initial.lo, initial.hi1, initial.lo1) == (0, 0, 0, 0)
    assert (with_hi.hi, with_hi.lo, with_hi.hi1, with_hi.lo1) == (1, 0, 0, 0)
    assert (with_lo.hi, with_lo.lo, with_lo.hi1, with_lo.lo1) == (1, 2, 0, 0)
    assert (with_hi1.hi, with_hi1.lo, with_hi1.hi1, with_hi1.lo1) == (1, 2, 3, 0)
    assert (complete.hi, complete.lo, complete.hi1, complete.lo1) == (1, 2, 3, 4)
    assert complete.write_lo1(4) is complete
    with pytest.raises(FrozenInstanceError):
        complete.hi = 5  # type: ignore[misc]


@pytest.mark.unit
@pytest.mark.parametrize("field_name", HILO_FIELDS)
def test_r5900_computed_hilo_writes_reject_non_integers(field_name: str) -> None:
    """Reject Python coercions that could conceal reference-model defects."""
    state = R5900State.initial()
    for value in (True, 1.0, "1"):
        with pytest.raises(TypeError):
            write_hilo(state, field_name, value)  # type: ignore[arg-type]


@pytest.mark.unit
def test_r5900_existing_successors_preserve_all_hilo_state() -> None:
    """Carry both pairs unchanged through PC, GPR, and instruction successors."""
    initial = R5900State.initial(start_pc=8, **INITIAL_VALUES)
    with_gpr = initial.write_gpr(7, GPR_SENTINEL)
    with_pc = with_gpr.write_pc(12)
    after_nop = with_pc.step(0)

    for state in (with_gpr, with_pc, after_nop):
        for field_name, expected in INITIAL_VALUES.items():
            assert getattr(state, field_name) == expected
    assert initial.read_gpr(7) == 0
    assert with_gpr.read_gpr(7) == GPR_SENTINEL
    assert after_nop.pc == EXPECTED_NOP_PC
