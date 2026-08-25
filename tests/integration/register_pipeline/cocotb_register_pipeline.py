"""Integration tests for two connected enabled-register instances."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

FIRST_VALUE = 0x1111_2222
SECOND_VALUE = 0x3333_4444


async def sample_after_rising_edge(dut) -> int:
    """Sample q_o after both sequential stages settle for one rising edge."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    value = int(dut.q_o.value)
    await Timer(1, unit="ns")
    return value


@cocotb.test()
async def propagate_across_two_register_instances(dut) -> None:
    """Check reset, one-cycle propagation, and upstream hold behavior."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())

    dut.rst_ni.value = 0
    dut.en_i.value = 0
    dut.d_i.value = 0
    assert await sample_after_rising_edge(dut) == 0

    dut.rst_ni.value = 1
    dut.en_i.value = 1
    dut.d_i.value = FIRST_VALUE
    assert await sample_after_rising_edge(dut) == 0

    dut.d_i.value = SECOND_VALUE
    assert await sample_after_rising_edge(dut) == FIRST_VALUE

    dut.en_i.value = 0
    dut.d_i.value = 0xDEAD_BEEF
    assert await sample_after_rising_edge(dut) == SECOND_VALUE

    dut.rst_ni.value = 0
    assert await sample_after_rising_edge(dut) == 0
