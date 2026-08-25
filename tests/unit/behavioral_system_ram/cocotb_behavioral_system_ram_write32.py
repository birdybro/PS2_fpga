"""Directed aligned 32-bit writes for behavioral system RAM."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

RAM_SIZE = 256
WRITE_VECTORS = {
    0: 0x6745_2301,
    4: 0xEFCD_AB89,
    RAM_SIZE - 4: 0x7654_3210,
}
FULL_WORD_STROBE = 0x000F


def drive_idle(dut) -> None:
    """Drive known inactive bus and backdoor controls."""
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


async def cycle(dut) -> tuple[int, int, int, int]:
    """Advance one edge and sample request and response outputs."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    sample = (
        int(dut.req_ready_o.value),
        int(dut.rsp_valid_o.value),
        int(dut.rsp_rdata_o.value),
        int(dut.rsp_error_o.value),
    )
    await Timer(1, unit="ns")
    return sample


async def read_backdoor_byte(dut, address: int) -> int:
    """Read one stored byte through the simulation-only backdoor."""
    dut.backdoor_addr_i.value = address
    await Timer(1, unit="ns")
    assert int(dut.backdoor_in_bounds_o.value) == 1
    return int(dut.backdoor_rdata_o.value)


async def request_write32(dut, address: int, value: int, *, stall_cycles: int = 0) -> None:
    """Issue one full-word write and consume its response."""
    dut.req_valid_i.value = 1
    dut.req_write_i.value = 1
    dut.req_addr_i.value = address
    dut.req_size_i.value = 2
    dut.req_wdata_i.value = value
    dut.req_wstrb_i.value = FULL_WORD_STROBE
    dut.rsp_ready_i.value = 0
    await Timer(1, unit="ns")
    assert int(dut.req_ready_o.value) == 1

    _, response_valid, response_data, response_error = await cycle(dut)
    dut.req_valid_i.value = 0
    assert (response_valid, response_data, response_error) == (1, 0, 0)

    for _ in range(stall_cycles):
        assert await cycle(dut) == (0, 1, 0, 0)

    dut.rsp_ready_i.value = 1
    _, response_valid, _, _ = await cycle(dut)
    assert response_valid == 0
    dut.rsp_ready_i.value = 0


async def request_read32(dut, address: int) -> int:
    """Read one word back through the architectural transaction interface."""
    dut.req_valid_i.value = 1
    dut.req_write_i.value = 0
    dut.req_addr_i.value = address
    dut.req_size_i.value = 2
    await Timer(1, unit="ns")
    assert int(dut.req_ready_o.value) == 1
    _, response_valid, response_data, response_error = await cycle(dut)
    dut.req_valid_i.value = 0
    assert (response_valid, response_error) == (1, 0)
    dut.rsp_ready_i.value = 1
    await cycle(dut)
    dut.rsp_ready_i.value = 0
    return response_data & 0xFFFF_FFFF


@cocotb.test()
async def aligned_write32_is_little_endian_full_word_and_backpressured(dut) -> None:
    """Write boundary words and reject malformed or unsupported requests."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    drive_idle(dut)
    dut.rst_ni.value = 0
    await cycle(dut)
    dut.rst_ni.value = 1

    for index, (address, value) in enumerate(WRITE_VECTORS.items()):
        await request_write32(dut, address, value, stall_cycles=2 if index == 0 else 0)
        expected_bytes = value.to_bytes(4, byteorder="little", signed=False)
        actual_bytes = bytes(
            [await read_backdoor_byte(dut, address + offset) for offset in range(4)]
        )
        assert actual_bytes == expected_bytes
        assert await request_read32(dut, address) == value

    invalid_requests = (
        (0, 2, 0x0010),
        (0, 1, FULL_WORD_STROBE),
        (2, 2, FULL_WORD_STROBE),
        (RAM_SIZE, 2, FULL_WORD_STROBE),
    )
    for address, size, strobe in invalid_requests:
        dut.req_valid_i.value = 1
        dut.req_write_i.value = 1
        dut.req_addr_i.value = address
        dut.req_size_i.value = size
        dut.req_wstrb_i.value = strobe
        await Timer(1, unit="ns")
        assert int(dut.req_ready_o.value) == 0
        await cycle(dut)
    drive_idle(dut)
