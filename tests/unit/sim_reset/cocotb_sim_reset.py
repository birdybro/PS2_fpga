"""Directed edge-count test for the simulation-only reset sequencer."""

from decimal import Decimal

import cocotb
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer
from cocotb.utils import get_sim_time

RESET_CYCLES = 4
FIRST_RISING_EDGE_NS = Decimal(5)
CLOCK_PERIOD_NS = Decimal(10)


def simulation_time_ns() -> Decimal:
    """Return exact simulation time expressed in nanoseconds."""
    return Decimal(str(get_sim_time(unit="ns")))


async def sample_after_clock_edge(dut) -> tuple[int, Decimal]:
    """Sample reset after all processes triggered by one rising edge settle."""
    await RisingEdge(dut.clk_o)
    await ReadOnly()
    reset_n = int(dut.rst_no.value)
    edge_time = simulation_time_ns()
    await Timer(1, unit="ps")
    return reset_n, edge_time


@cocotb.test()
async def reset_holds_for_exact_edge_count_and_stays_released(dut) -> None:
    """Require four asserted edges, falling-edge release, and stable deassertion."""
    await Timer(1, unit="ps")
    assert int(dut.clk_o.value) == 0
    assert int(dut.rst_no.value) == 0

    samples = [await sample_after_clock_edge(dut) for _ in range(RESET_CYCLES)]
    assert [reset_n for reset_n, _ in samples] == [0] * RESET_CYCLES
    assert samples[-1][1] == FIRST_RISING_EDGE_NS + CLOCK_PERIOD_NS * (RESET_CYCLES - 1)

    await FallingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.rst_no.value) == 1
    assert simulation_time_ns() == FIRST_RISING_EDGE_NS + CLOCK_PERIOD_NS * (
        RESET_CYCLES - Decimal("0.5")
    )
    await Timer(1, unit="ps")

    for _ in range(3):
        reset_n, _ = await sample_after_clock_edge(dut)
        assert reset_n == 1
