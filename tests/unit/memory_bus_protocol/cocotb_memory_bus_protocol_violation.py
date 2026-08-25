"""Inject one selected internal memory bus protocol violation."""

import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb_memory_bus_protocol_valid import cycle, drive_idle, reset_checker


async def violate_unsupported_size(dut) -> None:
    dut.req_valid_i.value = 1
    dut.req_size_i.value = 5
    await RisingEdge(dut.clk_i)


async def violate_request_stability(dut) -> None:
    dut.req_valid_i.value = 1
    dut.req_addr_i.value = 0x1000
    await cycle(dut)
    dut.req_addr_i.value = 0x2000
    await RisingEdge(dut.clk_i)


async def violate_request_withdrawal(dut) -> None:
    dut.req_valid_i.value = 1
    await cycle(dut)
    dut.req_valid_i.value = 0
    await RisingEdge(dut.clk_i)


async def violate_response_stability(dut) -> None:
    dut.req_valid_i.value = 1
    dut.req_ready_i.value = 1
    await cycle(dut)
    drive_idle(dut)
    dut.rsp_valid_i.value = 1
    dut.rsp_rdata_i.value = 0x1111
    await cycle(dut)
    dut.rsp_rdata_i.value = 0x2222
    await RisingEdge(dut.clk_i)


async def violate_response_withdrawal(dut) -> None:
    dut.req_valid_i.value = 1
    dut.req_ready_i.value = 1
    await cycle(dut)
    drive_idle(dut)
    dut.rsp_valid_i.value = 1
    await cycle(dut)
    dut.rsp_valid_i.value = 0
    await RisingEdge(dut.clk_i)


async def violate_response_causality(dut) -> None:
    dut.rsp_valid_i.value = 1
    await RisingEdge(dut.clk_i)


async def violate_single_outstanding(dut) -> None:
    dut.req_valid_i.value = 1
    dut.req_ready_i.value = 1
    await cycle(dut)
    await RisingEdge(dut.clk_i)


VIOLATIONS = {
    "unsupported_size": violate_unsupported_size,
    "request_stability": violate_request_stability,
    "request_withdrawal": violate_request_withdrawal,
    "response_stability": violate_response_stability,
    "response_withdrawal": violate_response_withdrawal,
    "response_causality": violate_response_causality,
    "single_outstanding": violate_single_outstanding,
}


@cocotb.test()
async def selected_violation_is_fatal(dut) -> None:
    """Drive the violation named by the outer assertion-validation harness."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    await reset_checker(dut)
    scenario = os.environ["PROTOCOL_VIOLATION"]
    await VIOLATIONS[scenario](dut)
    await Timer(20, unit="ns")
    raise AssertionError(f"protocol violation {scenario} did not terminate simulation")
