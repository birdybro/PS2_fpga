"""Differential aligned 32-bit behavioral RAM writes and readback."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

from reference.common.byte_memory import ByteMemoryModel

RAM_SIZE = 256
FULL_WORD_STROBE = 0x000F


async def cycle(dut) -> tuple[int, int]:
    """Advance one rising edge and return response valid and data."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    sample = int(dut.rsp_valid_o.value), int(dut.rsp_rdata_o.value)
    await Timer(1, unit="ns")
    return sample


async def rtl_write32(dut, address: int, value: int) -> None:
    """Issue and consume one aligned full-word bus write."""
    dut.req_valid_i.value = 1
    dut.req_write_i.value = 1
    dut.req_addr_i.value = address
    dut.req_wdata_i.value = value
    dut.req_wstrb_i.value = FULL_WORD_STROBE
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
    """Issue and consume one aligned bus read for writeback comparison."""
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
async def every_aligned_write_and_readback_matches_independent_model(dut) -> None:
    """Fill all words through RTL writes and compare every result to Python."""
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

    expected_words: dict[int, int] = {}
    for iteration, address in enumerate(range(0, RAM_SIZE, 4)):
        value = ((iteration * 0x9E37_79B9) ^ 0xA5C3_1F07) & 0xFFFF_FFFF
        expected_words[address] = value
        model.write32(address, value)
        await rtl_write32(dut, address, value)

    for iteration, (address, expected) in enumerate(expected_words.items()):
        assert model.read32(address) == expected
        actual = await rtl_read32(dut, address)
        assert actual == expected, (
            f"iteration={iteration} address=0x{address:08x} "
            f"expected=0x{expected:08x} actual=0x{actual:08x}"
        )
