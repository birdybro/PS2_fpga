"""Directed boundary tests for the simulation cycle watchdog."""

import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

MAX_CYCLES = int(os.environ["SIM_TIMEOUT_CYCLES"])
DISABLED_OBSERVATION_CYCLES = 8
STICKY_OBSERVATION_CYCLES = 2


async def sample_cycle(dut) -> tuple[int, int]:
    """Advance one clock edge and sample settled watchdog outputs."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    sample = (int(dut.timeout_o.value), int(dut.cycle_count_o.value))
    await Timer(1, unit="ns")
    return sample


@cocotb.test()
async def watchdog_obeys_exact_boundary_reset_and_disable_contract(dut) -> None:
    """Check cycle N assertion, sticky status, reset clearing, and MAX_CYCLES zero."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    dut.rst_ni.value = 0
    assert await sample_cycle(dut) == (0, 0)
    dut.rst_ni.value = 1

    if MAX_CYCLES == 0:
        for _ in range(DISABLED_OBSERVATION_CYCLES):
            assert await sample_cycle(dut) == (0, 0)
        return

    for expected_cycle in range(1, MAX_CYCLES + 1):
        assert await sample_cycle(dut) == (
            int(expected_cycle == MAX_CYCLES),
            expected_cycle,
        )

    for _ in range(STICKY_OBSERVATION_CYCLES):
        assert await sample_cycle(dut) == (1, MAX_CYCLES)

    dut.rst_ni.value = 0
    assert await sample_cycle(dut) == (0, 0)
