"""Differential byte-enabled 64-bit behavioral RAM writes."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

from reference.common.byte_memory import ByteMemoryModel

RAM_SIZE = 256
DOUBLEWORD_COUNT = RAM_SIZE // 8


async def cycle(dut) -> tuple[int, int]:
    """Advance one rising edge and return response valid and data."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    sample = int(dut.rsp_valid_o.value), int(dut.rsp_rdata_o.value)
    await Timer(1, unit="ns")
    return sample


async def initialize_byte(dut, model: ByteMemoryModel, address: int, value: int) -> None:
    """Initialize one byte in RTL storage and the independent model."""
    model.write_byte(address, value)
    dut.backdoor_addr_i.value = address
    dut.backdoor_wdata_i.value = value
    dut.backdoor_write_i.value = 1
    await cycle(dut)
    dut.backdoor_write_i.value = 0


async def rtl_write64_masked(dut, address: int, value: int, strobe: int) -> None:
    """Issue and consume one byte-enabled 64-bit bus write."""
    dut.req_valid_i.value = 1
    dut.req_write_i.value = 1
    dut.req_addr_i.value = address
    dut.req_wdata_i.value = value
    dut.req_wstrb_i.value = strobe
    await Timer(1, unit="ns")
    assert int(dut.req_ready_o.value) == 1
    response_valid, response_data = await cycle(dut)
    dut.req_valid_i.value = 0
    assert (response_valid, response_data, int(dut.rsp_error_o.value)) == (1, 0, 0)
    dut.rsp_ready_i.value = 1
    response_valid, _ = await cycle(dut)
    assert response_valid == 0
    dut.rsp_ready_i.value = 0


async def rtl_read64(dut, address: int) -> int:
    """Read one doubleword for full-image post-write comparison."""
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
    return response_data & 0xFFFF_FFFF_FFFF_FFFF


@cocotb.test()
async def every_write64_strobe_matches_independent_full_image_model(dut) -> None:
    """Apply all 256 masks across RAM and compare every resulting doubleword."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    model = ByteMemoryModel(RAM_SIZE)

    dut.rst_ni.value = 0
    dut.backdoor_write_i.value = 0
    dut.backdoor_addr_i.value = 0
    dut.backdoor_wdata_i.value = 0
    dut.req_valid_i.value = 0
    dut.req_write_i.value = 0
    dut.req_addr_i.value = 0
    dut.req_size_i.value = 3
    dut.req_wdata_i.value = 0
    dut.req_wstrb_i.value = 0
    dut.rsp_ready_i.value = 0
    await cycle(dut)
    dut.rst_ni.value = 1

    for address in range(RAM_SIZE):
        value = ((address * 197) ^ (address >> 1) ^ 0xB7) & 0xFF
        await initialize_byte(dut, model, address, value)

    for iteration in range(256):
        address = (iteration % DOUBLEWORD_COUNT) * 8
        value = ((iteration * 0x9E37_79B9_7F4A_7C15) ^ 0xD1B5_4A32_D192_ED03) & ((1 << 64) - 1)
        strobe = iteration
        model.write64_masked(address, value, strobe)
        await rtl_write64_masked(dut, address, value, strobe)

    for iteration, address in enumerate(range(0, RAM_SIZE, 8)):
        expected = model.read64(address)
        actual = await rtl_read64(dut, address)
        assert actual == expected, (
            f"iteration={iteration} address=0x{address:08x} "
            f"expected=0x{expected:016x} actual=0x{actual:016x}"
        )
