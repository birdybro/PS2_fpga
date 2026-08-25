"""Directed configurable response-latency tests for behavioral system RAM."""

import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

RESPONSE_LATENCY = int(os.environ["RAM_RESPONSE_LATENCY"])
READ_BYTES = bytes((0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF))
EXPECTED_READ = int.from_bytes(READ_BYTES, byteorder="little", signed=False)
WRITE_ADDRESS = 16
WRITE_DATA = 0x7856_3412
FULL_WORD_STROBE = 0x000F
MUTATED_BYTE = 0xFF


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


async def backdoor_write_byte(dut, address: int, value: int) -> None:
    """Initialize one storage byte through the simulation-only backdoor."""
    dut.backdoor_addr_i.value = address
    dut.backdoor_wdata_i.value = value
    dut.backdoor_write_i.value = 1
    await cycle(dut)
    dut.backdoor_write_i.value = 0


async def wait_for_delayed_response(dut, expected_data: int) -> None:
    """Check every inserted wait cycle and the exact completion edge."""
    for wait_index in range(RESPONSE_LATENCY):
        ready, valid, data, error = await cycle(dut)
        assert ready == 0
        assert valid == int(wait_index == RESPONSE_LATENCY - 1)
        assert error == 0
        if valid:
            assert data == expected_data


async def verify_captured_read_latency(dut) -> None:
    """Confirm exact read delay and acceptance-time data capture."""
    dut.req_valid_i.value = 1
    dut.req_write_i.value = 0
    dut.req_addr_i.value = 0
    dut.req_size_i.value = 3
    await Timer(1, unit="ns")
    assert int(dut.req_ready_o.value) == 1
    ready, valid, data, error = await cycle(dut)
    dut.req_valid_i.value = 0
    assert ready == 0
    assert valid == int(RESPONSE_LATENCY == 0)
    assert error == 0
    if valid:
        assert data == EXPECTED_READ

    dut.backdoor_addr_i.value = 0
    dut.backdoor_wdata_i.value = MUTATED_BYTE
    dut.backdoor_write_i.value = 1
    if RESPONSE_LATENCY == 0:
        assert await cycle(dut) == (0, 1, EXPECTED_READ, 0)
    else:
        for wait_index in range(RESPONSE_LATENCY):
            ready, valid, data, error = await cycle(dut)
            if wait_index == 0:
                dut.backdoor_write_i.value = 0
            assert ready == 0
            assert valid == int(wait_index == RESPONSE_LATENCY - 1)
            assert error == 0
            if valid:
                assert data == EXPECTED_READ
    dut.backdoor_write_i.value = 0

    assert await cycle(dut) == (0, 1, EXPECTED_READ, 0)
    assert int(dut.backdoor_rdata_o.value) == MUTATED_BYTE
    dut.rsp_ready_i.value = 1
    _, valid, _, _ = await cycle(dut)
    assert valid == 0
    dut.rsp_ready_i.value = 0


async def verify_write_latency(dut) -> None:
    """Confirm write side effects occur at acceptance before delayed completion."""
    dut.req_valid_i.value = 1
    dut.req_write_i.value = 1
    dut.req_addr_i.value = WRITE_ADDRESS
    dut.req_size_i.value = 2
    dut.req_wdata_i.value = WRITE_DATA
    dut.req_wstrb_i.value = FULL_WORD_STROBE
    await Timer(1, unit="ns")
    assert int(dut.req_ready_o.value) == 1
    _, valid, data, error = await cycle(dut)
    dut.req_valid_i.value = 0
    assert (valid, data, error) == (int(RESPONSE_LATENCY == 0), 0, 0)

    dut.backdoor_addr_i.value = WRITE_ADDRESS
    await Timer(1, unit="ns")
    assert int(dut.backdoor_rdata_o.value) == (WRITE_DATA & 0xFF)
    if RESPONSE_LATENCY > 0:
        await wait_for_delayed_response(dut, 0)
    assert await cycle(dut) == (0, 1, 0, 0)
    dut.rsp_ready_i.value = 1
    _, valid, _, _ = await cycle(dut)
    assert valid == 0
    dut.rsp_ready_i.value = 0


async def verify_reset_cancels_pending_response(dut) -> None:
    """Ensure reset discards a delayed response before it becomes visible."""
    if RESPONSE_LATENCY > 0:
        dut.req_valid_i.value = 1
        dut.req_write_i.value = 0
        dut.req_addr_i.value = 0
        dut.req_size_i.value = 2
        await Timer(1, unit="ns")
        assert int(dut.req_ready_o.value) == 1
        _, valid, _, _ = await cycle(dut)
        dut.req_valid_i.value = 0
        assert valid == 0

        dut.rst_ni.value = 0
        _, valid, _, _ = await cycle(dut)
        assert valid == 0
        dut.rst_ni.value = 1
        for _ in range(RESPONSE_LATENCY + 1):
            _, valid, _, _ = await cycle(dut)
            assert valid == 0


@cocotb.test()
async def configured_latency_delays_captured_reads_and_write_completions(dut) -> None:
    """Verify zero/positive delays, backpressure, side effects, and reset cancellation."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    drive_idle(dut)
    dut.rst_ni.value = 0
    await cycle(dut)
    dut.rst_ni.value = 1

    for address, value in enumerate(READ_BYTES):
        await backdoor_write_byte(dut, address, value)

    await verify_captured_read_latency(dut)
    await verify_write_latency(dut)
    await verify_reset_cancels_pending_response(dut)
