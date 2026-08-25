"""Deterministic stimulus for the memory transaction trace sink."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

WRITE_DATA = 0x0123_4567_89AB_CDEF_FEDC_BA98_7654_3210
FIRST_RESPONSE_DATA = 0x1111_2222_3333_4444_5555_6666_7777_8888
ERROR_RESPONSE_DATA = 0xFFFF_0000_FFFF_0000_AAAA_5555_AAAA_5555


def drive_idle(dut) -> None:
    """Drive known inactive values on every monitored signal."""
    dut.req_valid_i.value = 0
    dut.req_ready_i.value = 0
    dut.req_write_i.value = 0
    dut.req_addr_i.value = 0
    dut.req_size_i.value = 0
    dut.req_wdata_i.value = 0
    dut.req_wstrb_i.value = 0
    dut.rsp_valid_i.value = 0
    dut.rsp_ready_i.value = 0
    dut.rsp_rdata_i.value = 0
    dut.rsp_error_i.value = 0


async def cycle(dut) -> None:
    """Advance one edge after monitored state has settled."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    await Timer(1, unit="ns")


@cocotb.test()
async def trace_stimulus_covers_stalls_and_same_cycle_events(dut) -> None:
    """Drive reset, stalled transfers, and deterministic accepted transactions."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    drive_idle(dut)
    dut.rst_ni.value = 0
    dut.req_valid_i.value = 1
    dut.req_ready_i.value = 1
    await cycle(dut)

    dut.rst_ni.value = 1
    dut.req_ready_i.value = 0
    dut.req_addr_i.value = 0x1000
    dut.req_size_i.value = 2
    await cycle(dut)

    dut.req_ready_i.value = 1
    await cycle(dut)

    dut.req_write_i.value = 1
    dut.req_addr_i.value = 0x2000
    dut.req_size_i.value = 4
    dut.req_wdata_i.value = WRITE_DATA
    dut.req_wstrb_i.value = 0xFFFF
    dut.rsp_valid_i.value = 1
    dut.rsp_ready_i.value = 1
    dut.rsp_rdata_i.value = FIRST_RESPONSE_DATA
    await cycle(dut)

    dut.req_valid_i.value = 0
    dut.rsp_ready_i.value = 0
    dut.rsp_rdata_i.value = ERROR_RESPONSE_DATA
    dut.rsp_error_i.value = 1
    await cycle(dut)

    dut.rsp_ready_i.value = 1
    await cycle(dut)

    drive_idle(dut)
    await cycle(dut)
