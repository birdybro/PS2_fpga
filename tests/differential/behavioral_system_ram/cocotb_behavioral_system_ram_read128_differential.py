"""Differential aligned 128-bit behavioral RAM reads."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

from reference.common.byte_memory import ByteMemoryModel

RAM_SIZE = 256


async def cycle(dut) -> tuple[int, int]:
    """Advance one rising edge and return response valid and data."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    sample = int(dut.rsp_valid_o.value), int(dut.rsp_rdata_o.value)
    await Timer(1, unit="ns")
    return sample


async def initialize_byte(dut, model: ByteMemoryModel, address: int, value: int) -> None:
    """Write the same byte to RTL storage and the independent model."""
    model.write_byte(address, value)
    dut.backdoor_addr_i.value = address
    dut.backdoor_wdata_i.value = value
    dut.backdoor_write_i.value = 1
    await cycle(dut)
    dut.backdoor_write_i.value = 0


async def rtl_read128(dut, address: int) -> int:
    """Issue and consume one aligned 128-bit bus read."""
    dut.req_valid_i.value = 1
    dut.req_addr_i.value = address
    await Timer(1, unit="ns")
    assert int(dut.req_ready_o.value) == 1
    response_valid, response_data = await cycle(dut)
    dut.req_valid_i.value = 0
    assert response_valid == 1
    dut.rsp_ready_i.value = 1
    response_valid, _ = await cycle(dut)
    assert response_valid == 0
    dut.rsp_ready_i.value = 0
    return response_data


@cocotb.test()
async def every_aligned_quadword_matches_independent_byte_model(dut) -> None:
    """Compare every aligned quadword after asymmetric byte initialization."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    model = ByteMemoryModel(RAM_SIZE)

    dut.rst_ni.value = 0
    dut.backdoor_write_i.value = 0
    dut.backdoor_addr_i.value = 0
    dut.backdoor_wdata_i.value = 0
    dut.req_valid_i.value = 0
    dut.req_write_i.value = 0
    dut.req_addr_i.value = 0
    dut.req_size_i.value = 4
    dut.req_wdata_i.value = 0
    dut.req_wstrb_i.value = 0
    dut.rsp_ready_i.value = 0
    await cycle(dut)
    dut.rst_ni.value = 1

    for address in range(RAM_SIZE):
        value = ((address * 239) ^ (address >> 3) ^ 0x3B) & 0xFF
        await initialize_byte(dut, model, address, value)

    for iteration, address in enumerate(range(0, RAM_SIZE, 16)):
        expected = model.read128(address)
        actual = await rtl_read128(dut, address)
        assert actual == expected, (
            f"iteration={iteration} address=0x{address:08x} "
            f"expected=0x{expected:032x} actual=0x{actual:032x}"
        )
