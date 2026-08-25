"""Directed storage and bounds tests for the behavioral system RAM."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

RAM_SIZE = 256
INITIAL_VALUES = {
    0: 0x10,
    1: 0x21,
    RAM_SIZE - 2: 0xDC,
    RAM_SIZE - 1: 0xFE,
}


async def clock_edge(dut) -> None:
    """Advance one edge and leave the read-only scheduler phase."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    await Timer(1, unit="ns")


async def write_byte(dut, address: int, value: int) -> None:
    """Write one byte through the simulation backdoor."""
    dut.backdoor_addr_i.value = address
    dut.backdoor_wdata_i.value = value
    dut.backdoor_write_i.value = 1
    await clock_edge(dut)
    dut.backdoor_write_i.value = 0


async def read_byte(dut, address: int) -> tuple[int, int]:
    """Read one byte and its bounds indication through the backdoor."""
    dut.backdoor_addr_i.value = address
    await Timer(1, unit="ns")
    return int(dut.backdoor_rdata_o.value), int(dut.backdoor_in_bounds_o.value)


@cocotb.test()
async def byte_storage_bounds_and_reset_independence(dut) -> None:
    """Cover boundary bytes, reset retention, and rejected out-of-range writes."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    dut.rst_ni.value = 0
    dut.backdoor_write_i.value = 0
    dut.backdoor_addr_i.value = 0
    dut.backdoor_wdata_i.value = 0
    dut.req_valid_i.value = 0
    dut.req_write_i.value = 0
    dut.req_addr_i.value = 0
    dut.req_size_i.value = 0
    dut.req_wdata_i.value = 0
    dut.req_wstrb_i.value = 0
    dut.rsp_ready_i.value = 0
    await clock_edge(dut)
    dut.rst_ni.value = 1

    for address, value in INITIAL_VALUES.items():
        await write_byte(dut, address, value)
    for address, value in INITIAL_VALUES.items():
        assert await read_byte(dut, address) == (value, 1)

    assert await read_byte(dut, RAM_SIZE) == (0, 0)
    assert await read_byte(dut, RAM_SIZE + 0x55) == (0, 0)

    await write_byte(dut, RAM_SIZE, 0xAA)
    assert await read_byte(dut, 0) == (INITIAL_VALUES[0], 1)

    dut.rst_ni.value = 0
    dut.backdoor_addr_i.value = 0
    dut.backdoor_wdata_i.value = 0x77
    dut.backdoor_write_i.value = 1
    await clock_edge(dut)
    dut.backdoor_write_i.value = 0
    for address, value in INITIAL_VALUES.items():
        assert await read_byte(dut, address) == (value, 1)

    dut.rst_ni.value = 1
    await write_byte(dut, 0, 0x77)
    assert await read_byte(dut, 0) == (0x77, 1)
