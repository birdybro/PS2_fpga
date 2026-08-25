"""Legal ready/valid tests for the R5900 instruction-fetch request issuer."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
FETCH_SIZE_CODE = 2


async def edge(dut) -> None:
    """Advance one rising edge and allow sequential outputs to settle."""
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut) -> None:
    """Reset the request issuer with the target not ready."""
    dut.rst_ni.value = 0
    dut.start_i.value = 0
    dut.pc_i.value = 0
    dut.req_ready_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1


async def start_request(dut, address: int) -> None:
    """Pulse one aligned fetch start and wait for its latched request."""
    dut.pc_i.value = address
    dut.start_i.value = 1
    await edge(dut)
    dut.start_i.value = 0


def assert_read_word_request(dut, address: int) -> None:
    """Check every field of one 32-bit read request."""
    assert int(dut.req_valid_o.value) == 1
    assert int(dut.req_write_o.value) == 0
    assert int(dut.req_addr_o.value) == address
    assert int(dut.req_size_o.value) == FETCH_SIZE_CODE
    assert int(dut.req_wdata_o.value) == 0
    assert int(dut.req_wstrb_o.value) == 0


@cocotb.test()
async def test_r5900_fetch_issues_exact_32_bit_read_fields(dut) -> None:
    """Issue exact aligned requests at low, normal, and final word addresses."""
    await initialize(dut)
    for address in (0, 4, 0x0010_0000, 0xFFFF_FFFC):
        await start_request(dut, address)
        assert_read_word_request(dut, address)
        assert int(dut.accepted_o.value) == 0
        dut.req_ready_i.value = 1
        await Timer(1, unit="ns")
        assert int(dut.accepted_o.value) == 1
        await edge(dut)
        dut.req_ready_i.value = 0
        assert int(dut.req_valid_o.value) == 0
        assert int(dut.accepted_o.value) == 0


@cocotb.test()
async def test_r5900_fetch_holds_complete_request_under_backpressure(dut) -> None:
    """Keep all fields stable while PC and unrelated source inputs change."""
    await initialize(dut)
    address = 0x1234_5678
    await start_request(dut, address)
    assert_read_word_request(dut, address)

    for changed_pc in (0, 0xAAAA_AAAA, 0xFFFF_FFFC):
        dut.pc_i.value = changed_pc
        await edge(dut)
        assert_read_word_request(dut, address)
        assert int(dut.accepted_o.value) == 0


@cocotb.test()
async def test_r5900_fetch_accepts_once_and_reset_cancels_pending(dut) -> None:
    """Pulse completion for one handshake, then cancel a different stalled request."""
    await initialize(dut)
    await start_request(dut, 0x2000)
    dut.req_ready_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.accepted_o.value) == 1
    await edge(dut)
    assert int(dut.req_valid_o.value) == 0
    assert int(dut.accepted_o.value) == 0
    await edge(dut)
    assert int(dut.accepted_o.value) == 0

    dut.req_ready_i.value = 0
    await start_request(dut, 0x3000)
    assert int(dut.req_valid_o.value) == 1
    dut.rst_ni.value = 0
    await edge(dut)
    assert int(dut.req_valid_o.value) == 0
    assert int(dut.accepted_o.value) == 0
