"""Deterministic randomized verification of the common enabled register."""

import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

BOUNDARY_VALUES = (
    0x0000_0000,
    0x0000_0001,
    0x7FFF_FFFF,
    0x8000_0000,
    0xFFFF_FFFF,
    0xAAAA_AAAA,
    0x5555_5555,
)
RANDOM_CASES = 121


async def sample_after_rising_edge(dut) -> int:
    """Sample q_o after sequential assignments settle for one rising edge."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    value = int(dut.q_o.value)
    await Timer(1, unit="ns")
    return value


@cocotb.test()
async def randomized_reset_enable_and_data(dut) -> None:
    """Compare seeded register transitions against a small state model."""
    seed = cocotb.RANDOM_SEED
    rng = random.Random(seed)
    values = (*BOUNDARY_VALUES, *(rng.getrandbits(32) for _ in range(RANDOM_CASES)))
    expected = 0

    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    for iteration, value in enumerate(values):
        reset_active = iteration % 37 == 0
        enabled = bool(rng.getrandbits(1))
        dut.rst_ni.value = not reset_active
        dut.en_i.value = enabled
        dut.d_i.value = value

        if reset_active:
            expected = 0
        elif enabled:
            expected = value

        actual = await sample_after_rising_edge(dut)
        assert actual == expected, (
            f"seed={seed} iteration={iteration} reset={reset_active} "
            f"enable={enabled} data=0x{value:08x} "
            f"expected=0x{expected:08x} actual=0x{actual:08x}"
        )
