"""Exhaustive differential byte-enabled 128-bit behavioral RAM writes."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

from reference.common.byte_memory import ByteMemoryModel

RAM_SIZE = 256
QUADWORD_MASK = 0x0F
VALUE_MASK = (1 << 128) - 1
VALUE_MULTIPLIER = 0x9E37_79B9_7F4A_7C15_F39C_C060_5CED_C835
VALUE_OFFSET = 0xD1B5_4A32_D192_ED03_ABC9_8388_FB8F_AC03


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


async def rtl_read128(dut, address: int) -> int:
    """Read one quadword for full-image post-write comparison."""
    dut.req_valid_i.value = 1
    dut.req_write_i.value = 0
    dut.req_addr_i.value = address
    dut.req_wstrb_i.value = 0
    dut.rsp_ready_i.value = 0
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
async def every_write128_strobe_matches_independent_full_image_model(dut) -> None:
    """Pipeline all 65,536 masks, then compare every resulting quadword."""
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
        value = ((address * 211) ^ (address >> 2) ^ 0xC9) & 0xFF
        await initialize_byte(dut, model, address, value)

    dut.rsp_ready_i.value = 1
    for strobe in range(1 << 16):
        address = (((strobe >> 8) ^ strobe) & QUADWORD_MASK) * 16
        value = ((strobe * VALUE_MULTIPLIER) ^ VALUE_OFFSET) & VALUE_MASK
        model.write128_masked(address, value, strobe)
        dut.req_valid_i.value = 1
        dut.req_write_i.value = 1
        dut.req_addr_i.value = address
        dut.req_wdata_i.value = value
        dut.req_wstrb_i.value = strobe
        await Timer(1, unit="ns")
        assert int(dut.req_ready_o.value) == 1
        response_valid, response_data = await cycle(dut)
        assert (response_valid, response_data, int(dut.rsp_error_o.value)) == (1, 0, 0)

    dut.req_valid_i.value = 0
    response_valid, _ = await cycle(dut)
    assert response_valid == 0
    dut.rsp_ready_i.value = 0

    for iteration, address in enumerate(range(0, RAM_SIZE, 16)):
        expected = model.read128(address)
        actual = await rtl_read128(dut, address)
        assert actual == expected, (
            f"iteration={iteration} address=0x{address:08x} "
            f"expected=0x{expected:032x} actual=0x{actual:032x}"
        )
