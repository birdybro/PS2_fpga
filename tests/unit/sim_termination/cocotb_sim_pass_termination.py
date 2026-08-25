"""Directed one-shot tests for simulation PASS state."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer


async def sample_cycle(dut) -> tuple[int, int]:
    """Advance one rising edge and sample settled PASS outputs."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    sample = (int(dut.pass_event_o.value), int(dut.pass_latched_o.value))
    await Timer(1, unit="ns")
    return sample


@cocotb.test()
async def pass_is_one_shot_per_reset_epoch(dut) -> None:
    """Ignore reset-time requests, pulse once, latch, and re-arm only on reset."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    dut.rst_ni.value = 0
    dut.pass_i.value = 1
    assert await sample_cycle(dut) == (0, 0)

    dut.rst_ni.value = 1
    dut.pass_i.value = 0
    assert await sample_cycle(dut) == (0, 0)
    dut.pass_i.value = 1
    assert await sample_cycle(dut) == (1, 1)

    for _ in range(2):
        assert await sample_cycle(dut) == (0, 1)
    dut.pass_i.value = 0
    assert await sample_cycle(dut) == (0, 1)
    dut.pass_i.value = 1
    assert await sample_cycle(dut) == (0, 1)

    dut.rst_ni.value = 0
    assert await sample_cycle(dut) == (0, 0)
    dut.rst_ni.value = 1
    assert await sample_cycle(dut) == (1, 1)
