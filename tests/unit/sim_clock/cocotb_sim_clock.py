"""Directed timing test for the simulation-only clock source."""

from decimal import Decimal
from itertools import pairwise

import cocotb
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from cocotb.utils import get_sim_time

EXPECTED_PERIOD_NS = Decimal(10)
EXPECTED_HALF_PERIOD_NS = EXPECTED_PERIOD_NS / 2


def simulation_time_ns() -> Decimal:
    """Return exact simulation time expressed in nanoseconds."""
    return Decimal(str(get_sim_time(unit="ns")))


@cocotb.test()
async def clock_starts_low_and_maintains_period(dut) -> None:
    """Measure initial level, rising-edge period, and 50-percent duty cycle."""
    await Timer(1, unit="ps")
    assert int(dut.clk_o.value) == 0

    rising_edges: list[Decimal] = []
    for _ in range(5):
        await RisingEdge(dut.clk_o)
        rising_edges.append(simulation_time_ns())

    assert rising_edges[0] == EXPECTED_HALF_PERIOD_NS
    assert [later - earlier for earlier, later in pairwise(rising_edges)] == [
        EXPECTED_PERIOD_NS
    ] * 4

    await FallingEdge(dut.clk_o)
    assert simulation_time_ns() - rising_edges[-1] == EXPECTED_HALF_PERIOD_NS
