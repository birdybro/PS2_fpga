"""Legal-transition tests for the R5900 functional control skeleton."""

from enum import IntEnum

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10


class State(IntEnum):
    """Independent numeric view of the published control-state sequence."""

    FETCH_REQUEST = 0
    FETCH_RESPONSE = 1
    DECODE = 2
    EXECUTE = 3
    WRITEBACK = 4


DONE_SIGNALS = (
    "fetch_request_done_i",
    "fetch_response_done_i",
    "decode_done_i",
    "execute_done_i",
    "writeback_done_i",
)


async def edge(dut) -> None:
    """Advance one edge and allow sequential state to settle."""
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut) -> None:
    """Start the clock and synchronously enter the fetch-request state."""
    dut.rst_ni.value = 0
    dut.inject_illegal_i.value = 0
    for signal in DONE_SIGNALS:
        getattr(dut, signal).value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1
    assert int(dut.state_o.value) == State.FETCH_REQUEST


async def complete(dut, signal: str, expected: State) -> None:
    """Pulse one completion and check the state reached on its edge."""
    getattr(dut, signal).value = 1
    await edge(dut)
    getattr(dut, signal).value = 0
    assert int(dut.state_o.value) == expected


@cocotb.test()
async def test_r5900_control_holds_and_follows_complete_legal_sequence(dut) -> None:
    """Hold every state under stalls and traverse exactly one state per completion."""
    await initialize(dut)
    transitions = (
        ("fetch_request_done_i", State.FETCH_RESPONSE),
        ("fetch_response_done_i", State.DECODE),
        ("decode_done_i", State.EXECUTE),
        ("execute_done_i", State.WRITEBACK),
        ("writeback_done_i", State.FETCH_REQUEST),
    )
    for signal, expected in transitions:
        current = int(dut.state_o.value)
        for _ in range(2):
            await edge(dut)
            assert int(dut.state_o.value) == current
        await complete(dut, signal, expected)


@cocotb.test()
async def test_r5900_control_ignores_irrelevant_completions_and_reset_wins(dut) -> None:
    """Prevent skips when unrelated events assert and return any state to fetch request."""
    await initialize(dut)
    dut.fetch_response_done_i.value = 1
    dut.decode_done_i.value = 1
    dut.execute_done_i.value = 1
    dut.writeback_done_i.value = 1
    await edge(dut)
    assert int(dut.state_o.value) == State.FETCH_REQUEST

    dut.fetch_request_done_i.value = 1
    await edge(dut)
    assert int(dut.state_o.value) == State.FETCH_RESPONSE

    dut.rst_ni.value = 0
    await edge(dut)
    assert int(dut.state_o.value) == State.FETCH_REQUEST
