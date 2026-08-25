"""Differential 32-bit byte-enable behavioral RAM writes."""

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
    """Initialize one byte in both the RTL storage and Python model."""
    model.write_byte(address, value)
    dut.backdoor_addr_i.value = address
    dut.backdoor_wdata_i.value = value
    dut.backdoor_write_i.value = 1
    await cycle(dut)
    dut.backdoor_write_i.value = 0


async def rtl_write32_masked(dut, address: int, value: int, strobe: int) -> None:
    """Issue and consume one byte-enabled 32-bit bus write."""
    dut.req_valid_i.value = 1
    dut.req_write_i.value = 1
    dut.req_addr_i.value = address
    dut.req_wdata_i.value = value
    dut.req_wstrb_i.value = strobe
    await Timer(1, unit="ns")
    assert int(dut.req_ready_o.value) == 1
    response_valid, response_data = await cycle(dut)
    dut.req_valid_i.value = 0
    assert (response_valid, response_data) == (1, 0)
    dut.rsp_ready_i.value = 1
    response_valid, _ = await cycle(dut)
    assert response_valid == 0
    dut.rsp_ready_i.value = 0


async def rtl_read32(dut, address: int) -> int:
    """Read one complete word for post-write differential comparison."""
    dut.req_valid_i.value = 1
    dut.req_write_i.value = 0
    dut.req_addr_i.value = address
    dut.req_wstrb_i.value = 0
    await Timer(1, unit="ns")
    assert int(dut.req_ready_o.value) == 1
    response_valid, response_data = await cycle(dut)
    dut.req_valid_i.value = 0
    assert response_valid == 1
    dut.rsp_ready_i.value = 1
    response_valid, _ = await cycle(dut)
    assert response_valid == 0
    dut.rsp_ready_i.value = 0
    return response_data & 0xFFFF_FFFF


@cocotb.test()
async def every_word_and_strobe_class_matches_independent_model(dut) -> None:
    """Apply all strobe patterns repeatedly and compare the resulting image."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    model = ByteMemoryModel(RAM_SIZE)

    dut.rst_ni.value = 0
    dut.backdoor_write_i.value = 0
    dut.backdoor_addr_i.value = 0
    dut.backdoor_wdata_i.value = 0
    dut.req_valid_i.value = 0
    dut.req_write_i.value = 0
    dut.req_addr_i.value = 0
    dut.req_size_i.value = 2
    dut.req_wdata_i.value = 0
    dut.req_wstrb_i.value = 0
    dut.rsp_ready_i.value = 0
    await cycle(dut)
    dut.rst_ni.value = 1

    for address in range(RAM_SIZE):
        value = ((address * 29) ^ 0x5A) & 0xFF
        await initialize_byte(dut, model, address, value)

    for iteration, address in enumerate(range(0, RAM_SIZE, 4)):
        value = ((iteration * 0x45D9_F3B) ^ 0xC3A5_7E19) & 0xFFFF_FFFF
        strobe = iteration % 16
        model.write32_masked(address, value, strobe)
        await rtl_write32_masked(dut, address, value, strobe)

    for iteration, address in enumerate(range(0, RAM_SIZE, 4)):
        expected = model.read32(address)
        actual = await rtl_read32(dut, address)
        assert actual == expected, (
            f"iteration={iteration} address=0x{address:08x} "
            f"expected=0x{expected:08x} actual=0x{actual:08x}"
        )
