"""Directed aligned 64-bit writes for behavioral system RAM."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

RAM_SIZE = 256
TEST_ADDRESS = 8
BASELINE_BYTES = bytes((0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88))
WRITE_BYTES = bytes((0xA1, 0xB2, 0xC3, 0xD4, 0xE5, 0xF6, 0x07, 0x18))
WRITE_DATA = int.from_bytes(WRITE_BYTES, byteorder="little", signed=False)
BACKPRESSURE_STROBE = 0xA5


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


async def backdoor_write_bytes(dut, address: int, values: bytes) -> None:
    """Initialize adjacent bytes before a masked bus write."""
    for lane, value in enumerate(values):
        dut.backdoor_addr_i.value = address + lane
        dut.backdoor_wdata_i.value = value
        dut.backdoor_write_i.value = 1
        await cycle(dut)
    dut.backdoor_write_i.value = 0


async def backdoor_read_bytes(dut, address: int) -> bytes:
    """Read eight adjacent bytes through the simulation backdoor."""
    values = []
    for lane in range(8):
        dut.backdoor_addr_i.value = address + lane
        await Timer(1, unit="ns")
        values.append(int(dut.backdoor_rdata_o.value))
    return bytes(values)


async def masked_write64(dut, address: int, strobe: int, *, stall_cycles: int = 0) -> None:
    """Issue and consume one byte-enabled 64-bit write."""
    dut.req_valid_i.value = 1
    dut.req_write_i.value = 1
    dut.req_addr_i.value = address
    dut.req_size_i.value = 3
    dut.req_wdata_i.value = WRITE_DATA
    dut.req_wstrb_i.value = strobe
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


def expected_bytes(strobe: int) -> bytes:
    """Compute expected storage without duplicating the RTL assignment structure."""
    return bytes(
        WRITE_BYTES[lane] if strobe & (1 << lane) else BASELINE_BYTES[lane] for lane in range(8)
    )


@cocotb.test()
async def aligned_write64_honors_every_byte_enable_and_backpressure(dut) -> None:
    """Exercise all 256 masks, boundaries, and invalid upper strobes."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    drive_idle(dut)
    dut.rst_ni.value = 0
    await cycle(dut)
    dut.rst_ni.value = 1

    for strobe in range(256):
        await backdoor_write_bytes(dut, TEST_ADDRESS, BASELINE_BYTES)
        await masked_write64(
            dut,
            TEST_ADDRESS,
            strobe,
            stall_cycles=2 if strobe == BACKPRESSURE_STROBE else 0,
        )
        assert await backdoor_read_bytes(dut, TEST_ADDRESS) == expected_bytes(strobe)

    for address, strobe in ((0, 0x01), (RAM_SIZE - 8, 0x80)):
        await backdoor_write_bytes(dut, address, BASELINE_BYTES)
        await masked_write64(dut, address, strobe)
        assert await backdoor_read_bytes(dut, address) == expected_bytes(strobe)

    for invalid_strobe in (0x0100, 0x8000, 0xFF00):
        dut.req_valid_i.value = 1
        dut.req_write_i.value = 1
        dut.req_addr_i.value = TEST_ADDRESS
        dut.req_size_i.value = 3
        dut.req_wstrb_i.value = invalid_strobe
        await Timer(1, unit="ns")
        assert int(dut.req_ready_o.value) == 0
        await cycle(dut)
    drive_idle(dut)
