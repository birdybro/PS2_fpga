"""Cocotb tests for reset-free R5900 HI, LO, HI1, and LO1 storage."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

HILO_WIDTH = 64
HILO_MASK = (1 << HILO_WIDTH) - 1
CLOCK_PERIOD_NS = 10
FIELD_NAMES = ("hi", "lo", "hi1", "lo1")
INITIAL_STATE = {
    "hi": 0x0123_4567_89AB_CDEF,
    "lo": 0xFEDC_BA98_7654_3210,
    "hi1": 0x8000_0000_0000_0001,
    "lo1": 0x7FFF_FFFF_FFFF_FFFE,
}
UPDATED_STATE = {
    "hi": HILO_MASK,
    "lo": 0,
    "hi1": 0xAAAA_5555_AAAA_5555,
    "lo1": 0x5555_AAAA_5555_AAAA,
}


def packed_state(values: dict[str, int]) -> int:
    """Pack fields in the declared SystemVerilog structure order."""
    return (values["hi"] << 192) | (values["lo"] << 128) | (values["hi1"] << 64) | values["lo1"]


async def start_clock(dut) -> None:
    """Start the clock with every independent write boundary disabled."""
    for field_name in FIELD_NAMES:
        getattr(dut, f"write_{field_name}_valid_i").value = 0
        getattr(dut, f"write_{field_name}_value_i").value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await Timer(1, unit="ns")


async def drive_writes(dut, values: dict[str, int], enabled: set[str]) -> None:
    """Drive one set of independent write controls without taking an edge."""
    for field_name in FIELD_NAMES:
        getattr(dut, f"write_{field_name}_valid_i").value = field_name in enabled
        getattr(dut, f"write_{field_name}_value_i").value = values[field_name]


async def seed_all_state(dut, values: dict[str, int]) -> None:
    """Initialize every unreset storage element before observing it."""
    await drive_writes(dut, values, set(FIELD_NAMES))
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")
    await drive_writes(dut, values, set())


def observed_state(dut) -> dict[str, int]:
    """Read all four individually exposed state outputs."""
    return {field_name: int(getattr(dut, f"{field_name}_o").value) for field_name in FIELD_NAMES}


@cocotb.test()
async def test_r5900_hilo_state_has_independent_full_width_fields(dut) -> None:
    """Seed every field and verify the individual and packed mappings."""
    await start_clock(dut)
    await seed_all_state(dut, INITIAL_STATE)

    assert observed_state(dut) == INITIAL_STATE
    assert int(dut.state_o.value) == packed_state(INITIAL_STATE)


@cocotb.test()
async def test_r5900_hilo_state_writes_each_field_without_cross_coupling(dut) -> None:
    """Update one field per edge while the other three retain their values."""
    await start_clock(dut)
    expected = dict(INITIAL_STATE)
    await seed_all_state(dut, expected)

    for field_name in FIELD_NAMES:
        expected[field_name] = UPDATED_STATE[field_name]
        await drive_writes(dut, UPDATED_STATE, {field_name})
        await RisingEdge(dut.clk_i)
        await Timer(1, unit="ns")
        assert observed_state(dut) == expected
        assert int(dut.state_o.value) == packed_state(expected)


@cocotb.test()
async def test_r5900_hilo_state_updates_only_after_the_write_edge(dut) -> None:
    """Expose old state before one simultaneous write and new state after it."""
    await start_clock(dut)
    await seed_all_state(dut, INITIAL_STATE)
    await drive_writes(dut, UPDATED_STATE, set(FIELD_NAMES))

    await Timer(1, unit="ns")
    assert observed_state(dut) == INITIAL_STATE
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    assert observed_state(dut) == UPDATED_STATE
    assert int(dut.state_o.value) == packed_state(UPDATED_STATE)


@cocotb.test()
async def test_r5900_hilo_state_holds_when_all_writes_are_disabled(dut) -> None:
    """Ignore changing write values across multiple disabled clock edges."""
    await start_clock(dut)
    await seed_all_state(dut, INITIAL_STATE)
    await drive_writes(dut, UPDATED_STATE, set())

    for _ in range(3):
        await RisingEdge(dut.clk_i)
    await ReadOnly()
    assert observed_state(dut) == INITIAL_STATE
    assert int(dut.state_o.value) == packed_state(INITIAL_STATE)
