"""Directed aligned 32-bit reads for behavioral system RAM."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

RAM_SIZE = 256
READ_VECTORS = {
    0: ([0x01, 0x23, 0x45, 0x67], 0x6745_2301),
    4: ([0x89, 0xAB, 0xCD, 0xEF], 0xEFCD_AB89),
    RAM_SIZE - 4: ([0x10, 0x32, 0x54, 0x76], 0x7654_3210),
}


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


async def request_read32(dut, address: int, *, stall_cycles: int = 0) -> int:
    """Issue one aligned read and return its 32-bit little-endian payload."""
    dut.req_valid_i.value = 1
    dut.req_write_i.value = 0
    dut.req_addr_i.value = address
    dut.req_size_i.value = 2
    dut.rsp_ready_i.value = 0
    await Timer(1, unit="ns")
    assert int(dut.req_ready_o.value) == 1

    _, response_valid, response_data, response_error = await cycle(dut)
    dut.req_valid_i.value = 0
    assert response_valid == 1
    assert response_error == 0
    assert response_data >> 32 == 0

    for _ in range(stall_cycles):
        ready, valid, held_data, held_error = await cycle(dut)
        assert (ready, valid, held_data, held_error) == (0, 1, response_data, 0)

    dut.rsp_ready_i.value = 1
    _, response_valid, _, _ = await cycle(dut)
    assert response_valid == 0
    dut.rsp_ready_i.value = 0
    return response_data & 0xFFFF_FFFF


@cocotb.test()
async def aligned_read32_is_little_endian_bounded_and_backpressured(dut) -> None:
    """Read low, interior, and final words while rejecting unsupported requests."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    drive_idle(dut)
    dut.rst_ni.value = 0
    await cycle(dut)
    dut.rst_ni.value = 1

    for base, (byte_values, _) in READ_VECTORS.items():
        for offset, value in enumerate(byte_values):
            await write_backdoor_byte(dut, base + offset, value)

    for index, (address, (_, expected)) in enumerate(READ_VECTORS.items()):
        assert await request_read32(dut, address, stall_cycles=2 if index == 0 else 0) == expected

    invalid_requests = (
        (0, 1, 2),
        (0, 0, 1),
        (2, 0, 2),
        (RAM_SIZE, 0, 2),
    )
    for address, write, size in invalid_requests:
        dut.req_valid_i.value = 1
        dut.req_addr_i.value = address
        dut.req_write_i.value = write
        dut.req_size_i.value = size
        await Timer(1, unit="ns")
        assert int(dut.req_ready_o.value) == 0
        await cycle(dut)
    drive_idle(dut)
