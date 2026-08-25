"""Legal ready/valid tests for the R5900 instruction-fetch response receiver."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10


async def edge(dut) -> None:
    """Advance one rising edge and allow sequential outputs to settle."""
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut) -> None:
    """Reset every response and downstream input."""
    dut.rst_ni.value = 0
    dut.request_accepted_i.value = 0
    dut.instruction_ready_i.value = 0
    dut.rsp_valid_i.value = 0
    dut.rsp_rdata_i.value = 0
    dut.rsp_error_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1


async def arm_response(dut) -> None:
    """Report one accepted request and leave the receiver waiting."""
    dut.request_accepted_i.value = 1
    await edge(dut)
    dut.request_accepted_i.value = 0
    assert int(dut.response_expected_o.value) == 1
    assert int(dut.rsp_ready_o.value) == 1


async def present_response(dut, payload: int, error: int) -> None:
    """Present one response, check its handshake, and complete the edge."""
    dut.rsp_rdata_i.value = payload
    dut.rsp_error_i.value = error
    dut.rsp_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.rsp_ready_o.value) == 1
    assert int(dut.response_accepted_o.value) == 1
    await edge(dut)
    dut.rsp_valid_i.value = 0
    await Timer(1, unit="ns")


async def consume_instruction(dut) -> None:
    """Consume the buffered instruction through its downstream handshake."""
    dut.instruction_ready_i.value = 1
    await edge(dut)
    dut.instruction_ready_i.value = 0
    assert int(dut.instruction_valid_o.value) == 0


@cocotb.test()
async def test_r5900_fetch_response_holds_instruction_under_backpressure(dut) -> None:
    """Capture once, then hold the instruction and error while decode stalls."""
    await initialize(dut)
    instruction = 0x3405_1234
    payload = (0xA55A << 112) | instruction
    await arm_response(dut)
    await present_response(dut, payload, 0)

    assert int(dut.response_expected_o.value) == 0
    assert int(dut.instruction_valid_o.value) == 1
    assert int(dut.instruction_o.value) == instruction
    assert int(dut.fetch_error_o.value) == 0
    assert int(dut.rsp_ready_o.value) == 0

    for changed_payload in (0, (1 << 128) - 1, 0xDEAD_BEEF):
        dut.rsp_rdata_i.value = changed_payload
        dut.rsp_error_i.value = 1
        await edge(dut)
        assert int(dut.instruction_valid_o.value) == 1
        assert int(dut.instruction_o.value) == instruction
        assert int(dut.fetch_error_o.value) == 0

    await consume_instruction(dut)


@cocotb.test()
async def test_r5900_fetch_response_maps_lower_word_and_error(dut) -> None:
    """Latch the little-endian low word and preserve independent bus errors."""
    await initialize(dut)
    cases = (
        (0x0000_0000, 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF, 0),
        (0xFFFF_FFFF, 0x0000_0000_0000_0000_0000_0000, 1),
        (0x89AB_CDEF, 0x0123_4567_89AB_CDEF_0123_4567, 0),
    )
    for instruction, upper_96, error in cases:
        await arm_response(dut)
        await present_response(dut, (upper_96 << 32) | instruction, error)
        assert int(dut.instruction_valid_o.value) == 1
        assert int(dut.instruction_o.value) == instruction
        assert int(dut.fetch_error_o.value) == error
        await consume_instruction(dut)


@cocotb.test()
async def test_r5900_fetch_response_accepts_same_cycle_and_resets_state(dut) -> None:
    """Accept a zero-wait response, then prove reset cancels all receiver state."""
    await initialize(dut)
    instruction = 0x0000_0000
    dut.request_accepted_i.value = 1
    dut.rsp_valid_i.value = 1
    dut.rsp_rdata_i.value = instruction
    await Timer(1, unit="ns")
    assert int(dut.rsp_ready_o.value) == 1
    assert int(dut.response_accepted_o.value) == 1
    await edge(dut)
    dut.request_accepted_i.value = 0
    dut.rsp_valid_i.value = 0
    assert int(dut.response_expected_o.value) == 0
    assert int(dut.instruction_valid_o.value) == 1
    assert int(dut.instruction_o.value) == instruction

    dut.rst_ni.value = 0
    await edge(dut)
    assert int(dut.response_expected_o.value) == 0
    assert int(dut.instruction_valid_o.value) == 0
    assert int(dut.instruction_o.value) == 0
    assert int(dut.fetch_error_o.value) == 0
    assert int(dut.rsp_ready_o.value) == 0
