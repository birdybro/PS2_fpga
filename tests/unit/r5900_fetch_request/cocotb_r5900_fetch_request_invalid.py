"""Assertion tests for invalid R5900 instruction-fetch request starts."""

import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10


@cocotb.test()
async def test_r5900_fetch_rejects_invalid_start(dut) -> None:
    """Trigger the requested alignment or stalled-restart invariant."""
    violation = os.environ["FETCH_REQUEST_VIOLATION"]
    dut.rst_ni.value = 0
    dut.start_i.value = 0
    dut.pc_i.value = 0
    dut.req_ready_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")
    dut.rst_ni.value = 1

    if violation == "alignment":
        dut.pc_i.value = 2
        dut.start_i.value = 1
    elif violation == "stalled_restart":
        dut.pc_i.value = 0x1000
        dut.start_i.value = 1
        await RisingEdge(dut.clk_i)
        await Timer(1, unit="ns")
        dut.pc_i.value = 0x2000
    else:
        raise AssertionError(f"unknown violation: {violation}")

    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")
