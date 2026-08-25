"""Assertion tests for invalid R5900 instruction-fetch response traffic."""

import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10


@cocotb.test()
async def test_r5900_fetch_response_rejects_invalid_traffic(dut) -> None:
    """Trigger an unsolicited response or an overlapping accepted request."""
    violation = os.environ["FETCH_RESPONSE_VIOLATION"]
    dut.rst_ni.value = 0
    dut.request_accepted_i.value = 0
    dut.instruction_ready_i.value = 0
    dut.rsp_valid_i.value = 0
    dut.rsp_rdata_i.value = 0
    dut.rsp_error_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")
    dut.rst_ni.value = 1

    if violation == "unexpected":
        dut.rsp_valid_i.value = 1
    elif violation == "overlap":
        dut.request_accepted_i.value = 1
        await RisingEdge(dut.clk_i)
        await Timer(1, unit="ns")
    else:
        raise AssertionError(f"unknown violation: {violation}")

    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")
