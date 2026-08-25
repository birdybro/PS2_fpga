"""Fatal-path test stimulus for the simulation cycle watchdog."""

import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

MAX_CYCLES = int(os.environ["SIM_TIMEOUT_CYCLES"])


@cocotb.test()
async def configured_watchdog_terminates_simulation(dut) -> None:
    """Release reset and fail explicitly if the fatal boundary is not reached."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    dut.rst_ni.value = 0
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")
    dut.rst_ni.value = 1

    for _ in range(MAX_CYCLES + 2):
        await RisingEdge(dut.clk_i)
        await Timer(1, unit="ns")
    raise AssertionError("configured watchdog did not terminate simulation")
