"""Directed aligned 64-bit reads for behavioral system RAM."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

RAM_SIZE = 256
READ_VECTORS = {
    0: (bytes((0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF)), 0xEFCD_AB89_6745_2301),
    8: (bytes((0x10, 0x32, 0x54, 0x76, 0x98, 0xBA, 0xDC, 0xFE)), 0xFEDC_BA98_7654_3210),
    RAM_SIZE - 8: (
        bytes((0x0F, 0x1E, 0x2D, 0x3C, 0x4B, 0x5A, 0x69, 0x78)),
        0x7869_5A4B_3C2D_1E0F,
    ),
}


def drive_idle(dut) -> None:
    """Drive known inactive bus and backdoor controls."""
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


async def cycle(dut) -> tuple[int, int, int, int]:
    """Advance one edge and sample the bus-facing outputs."""
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


async def write_backdoor_byte(dut, address: int, value: int) -> None:
    """Initialize one storage byte through the simulation-only backdoor."""
    dut.backdoor_addr_i.value = address
    dut.backdoor_wdata_i.value = value
    dut.backdoor_write_i.value = 1
    await cycle(dut)
    dut.backdoor_write_i.value = 0


async def request_read64(dut, address: int, *, stall_cycles: int = 0) -> int:
    """Issue one aligned read and return its 64-bit little-endian payload."""
    dut.req_valid_i.value = 1
    dut.req_write_i.value = 0
    dut.req_addr_i.value = address
    dut.req_size_i.value = 3
    dut.rsp_ready_i.value = 0
    await Timer(1, unit="ns")
    assert int(dut.req_ready_o.value) == 1

    _, response_valid, response_data, response_error = await cycle(dut)
    dut.req_valid_i.value = 0
    assert response_valid == 1
    assert response_error == 0
    assert response_data >> 64 == 0

    for _ in range(stall_cycles):
        ready, valid, held_data, held_error = await cycle(dut)
        assert (ready, valid, held_data, held_error) == (0, 1, response_data, 0)

    dut.rsp_ready_i.value = 1
    _, response_valid, _, _ = await cycle(dut)
    assert response_valid == 0
    dut.rsp_ready_i.value = 0
    return response_data & 0xFFFF_FFFF_FFFF_FFFF


@cocotb.test()
async def aligned_read64_is_little_endian_bounded_and_backpressured(dut) -> None:
    """Read boundary doublewords and reject unsupported 64-bit requests."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    drive_idle(dut)
    dut.rst_ni.value = 0
    await cycle(dut)
    dut.rst_ni.value = 1

    for base, (byte_values, _) in READ_VECTORS.items():
        for offset, value in enumerate(byte_values):
            await write_backdoor_byte(dut, base + offset, value)

    for index, (address, (_, expected)) in enumerate(READ_VECTORS.items()):
        actual = await request_read64(dut, address, stall_cycles=2 if index == 0 else 0)
        assert actual == expected

    invalid_requests = (
        (4, 0, 3, 0),
        (RAM_SIZE, 0, 3, 0),
        (0, 1, 3, 0x0100),
        (0, 0, 4, 0),
    )
    for address, write, size, strobe in invalid_requests:
        dut.req_valid_i.value = 1
        dut.req_addr_i.value = address
        dut.req_write_i.value = write
        dut.req_size_i.value = size
        dut.req_wstrb_i.value = strobe
        await Timer(1, unit="ns")
        assert int(dut.req_ready_o.value) == 0
        await cycle(dut)
    drive_idle(dut)
