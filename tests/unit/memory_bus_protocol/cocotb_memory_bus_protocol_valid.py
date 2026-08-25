"""Directed legal traffic for internal memory bus protocol assertions."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer


def drive_idle(dut) -> None:
    """Drive a fully known idle transaction interface."""
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


async def cycle(dut) -> int:
    """Advance through one checked rising edge and sample outstanding state."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    outstanding = int(dut.outstanding_o.value)
    await Timer(1, unit="ns")
    return outstanding


async def reset_checker(dut) -> None:
    """Apply reset for two checked edges and release between edges."""
    drive_idle(dut)
    dut.rst_ni.value = 0
    assert await cycle(dut) == 0
    assert await cycle(dut) == 0
    dut.rst_ni.value = 1


@cocotb.test()
async def legal_stalls_sizes_zero_latency_and_replacement_pass(dut) -> None:
    """Exercise every legal state transition without firing an assertion."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    await reset_checker(dut)

    dut.req_valid_i.value = 1
    dut.req_write_i.value = 1
    dut.req_addr_i.value = 0x1000
    dut.req_size_i.value = 4
    dut.req_wdata_i.value = 0x0123_4567_89AB_CDEF_FEDC_BA98_7654_3210
    dut.req_wstrb_i.value = 0xFFFF
    assert await cycle(dut) == 0
    assert await cycle(dut) == 0

    dut.req_ready_i.value = 1
    assert await cycle(dut) == 1
    dut.req_valid_i.value = 0
    dut.req_ready_i.value = 0

    dut.rsp_valid_i.value = 1
    dut.rsp_rdata_i.value = 0xA5A5_5A5A_0123_4567_F0F0_0F0F_89AB_CDEF
    assert await cycle(dut) == 1
    assert await cycle(dut) == 1
    dut.rsp_ready_i.value = 1
    assert await cycle(dut) == 0
    drive_idle(dut)

    for size in range(5):
        dut.req_valid_i.value = 1
        dut.req_ready_i.value = 1
        dut.req_size_i.value = size
        dut.rsp_valid_i.value = 1
        dut.rsp_ready_i.value = 1
        assert await cycle(dut) == 0
        drive_idle(dut)

    dut.req_valid_i.value = 1
    dut.req_ready_i.value = 1
    assert await cycle(dut) == 1
    dut.rsp_valid_i.value = 1
    dut.rsp_ready_i.value = 1
    assert await cycle(dut) == 1
    dut.req_valid_i.value = 0
    assert await cycle(dut) == 0
