"""Directed cocotb smoke tests for the common enabled register."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer


async def sample_after_rising_edge(dut) -> int:
    """Sample q_o after sequential assignments settle for one rising edge."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    value = int(dut.q_o.value)
    await Timer(1, unit="ns")
    return value


@cocotb.test()
async def reset_load_and_hold(dut) -> None:
    """Reset to zero, load on enable, and retain the value while disabled."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())

    dut.rst_ni.value = 0
    dut.en_i.value = 0
    dut.d_i.value = 0xFFFF_FFFF
    assert await sample_after_rising_edge(dut) == 0

    dut.rst_ni.value = 1
    dut.en_i.value = 1
    dut.d_i.value = 0xA5A5_5A5A
    assert await sample_after_rising_edge(dut) == 0xA5A5_5A5A

    dut.en_i.value = 0
    dut.d_i.value = 0xDEAD_BEEF
    assert await sample_after_rising_edge(dut) == 0xA5A5_5A5A
