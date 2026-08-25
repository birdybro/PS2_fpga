"""Directed 32-bit byte-enable tests for behavioral system RAM."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

RAM_SIZE = 256
TEST_ADDRESS = 8
BASELINE_BYTES = bytes((0x11, 0x22, 0x33, 0x44))
WRITE_BYTES = bytes((0xA1, 0xB2, 0xC3, 0xD4))
WRITE_DATA = int.from_bytes(WRITE_BYTES, byteorder="little", signed=False)


async def cycle(dut) -> tuple[int, int, int]:
    """Advance one edge and sample request ready and response state."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    sample = (
        int(dut.req_ready_o.value),
        int(dut.rsp_valid_o.value),
        int(dut.rsp_rdata_o.value),
    )
    await Timer(1, unit="ns")
    return sample


async def backdoor_write_byte(dut, address: int, value: int) -> None:
    """Initialize one byte before a masked bus write."""
    dut.backdoor_addr_i.value = address
    dut.backdoor_wdata_i.value = value
    dut.backdoor_write_i.value = 1
    await cycle(dut)
    dut.backdoor_write_i.value = 0


async def backdoor_read_bytes(dut, address: int) -> bytes:
    """Read four adjacent bytes through the simulation backdoor."""
    values = []
    for lane in range(4):
        dut.backdoor_addr_i.value = address + lane
        await Timer(1, unit="ns")
        values.append(int(dut.backdoor_rdata_o.value))
    return bytes(values)


async def masked_write32(dut, address: int, strobe: int) -> None:
    """Issue and consume one byte-enabled 32-bit write."""
    dut.req_valid_i.value = 1
    dut.req_write_i.value = 1
    dut.req_addr_i.value = address
    dut.req_size_i.value = 2
    dut.req_wdata_i.value = WRITE_DATA
    dut.req_wstrb_i.value = strobe
    dut.rsp_ready_i.value = 0
    await Timer(1, unit="ns")
    assert int(dut.req_ready_o.value) == 1
    _, response_valid, response_data = await cycle(dut)
    dut.req_valid_i.value = 0
    assert (response_valid, response_data, int(dut.rsp_error_o.value)) == (1, 0, 0)
    dut.rsp_ready_i.value = 1
    _, response_valid, _ = await cycle(dut)
    assert response_valid == 0
    dut.rsp_ready_i.value = 0


@cocotb.test()
async def every_32bit_byte_enable_pattern_preserves_disabled_lanes(dut) -> None:
    """Exercise all 16 masks and reject strobes above the transfer width."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
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

    for strobe in range(16):
        for lane, value in enumerate(BASELINE_BYTES):
            await backdoor_write_byte(dut, TEST_ADDRESS + lane, value)
        await masked_write32(dut, TEST_ADDRESS, strobe)
        expected = bytes(
            WRITE_BYTES[lane] if strobe & (1 << lane) else BASELINE_BYTES[lane] for lane in range(4)
        )
        assert await backdoor_read_bytes(dut, TEST_ADDRESS) == expected

    for address, strobe in ((0, 0x0001), (RAM_SIZE - 4, 0x0008)):
        await masked_write32(dut, address, strobe)

    for invalid_strobe in (0x0010, 0x8000, 0xF00F):
        dut.req_valid_i.value = 1
        dut.req_write_i.value = 1
        dut.req_addr_i.value = TEST_ADDRESS
        dut.req_wstrb_i.value = invalid_strobe
        await Timer(1, unit="ns")
        assert int(dut.req_ready_o.value) == 0
        await cycle(dut)
