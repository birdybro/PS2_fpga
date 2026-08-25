"""Differential cocotb tests for the common enabled register."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

from reference.common.register_en import RegisterEnModel

TRANSITIONS = (
    (False, False, 0xFFFF_FFFF),
    (True, True, 0x0000_0000),
    (True, True, 0x0000_0001),
    (True, False, 0xDEAD_BEEF),
    (True, True, 0x7FFF_FFFF),
    (True, True, 0x8000_0000),
    (True, True, 0xFFFF_FFFF),
    (False, True, 0xAAAA_AAAA),
    (True, False, 0x5555_5555),
)


async def sample_after_rising_edge(dut) -> int:
    """Sample q_o after sequential assignments settle for one rising edge."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    value = int(dut.q_o.value)
    await Timer(1, unit="ns")
    return value


@cocotb.test()
async def compare_state_transitions_to_python_model(dut) -> None:
    """Compare reset, boundary loads, and holds to an independent state model."""
    model = RegisterEnModel(width=32)
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())

    for iteration, (reset_n, enable, data) in enumerate(TRANSITIONS):
        dut.rst_ni.value = reset_n
        dut.en_i.value = enable
        dut.d_i.value = data
        expected = model.tick(reset_n=reset_n, enable=enable, data=data)
        actual = await sample_after_rising_edge(dut)
        assert actual == expected, (
            f"iteration={iteration} reset_n={reset_n} enable={enable} "
            f"data=0x{data:08x} expected=0x{expected:08x} actual=0x{actual:08x}"
        )
