"""Assertion injection for the R5900 functional control state."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10


@cocotb.test()
async def test_r5900_control_rejects_illegal_state(dut) -> None:
    """Inject an unreachable enum value and require the RTL invariant to terminate."""
    dut.rst_ni.value = 0
    dut.inject_illegal_i.value = 0
    dut.fetch_request_done_i.value = 0
    dut.fetch_response_done_i.value = 0
    dut.decode_done_i.value = 0
    dut.execute_done_i.value = 0
    dut.writeback_done_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")
    dut.rst_ni.value = 1
    dut.inject_illegal_i.value = 1
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")
