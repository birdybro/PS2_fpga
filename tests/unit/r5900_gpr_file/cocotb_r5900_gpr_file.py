"""Cocotb tests for the architectural R5900 hardwired-zero GPR boundary."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

GPR_COUNT = 32
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
CLOCK_PERIOD_NS = 10


def register_value(index: int) -> int:
    """Return an asymmetric 128-bit value for one architectural GPR."""
    return ((1 << 127) | (index << 88) | (index << 56) | (index << 24) | index) & GPR_MASK


async def start_clock(dut) -> None:
    """Start the clock with inactive write controls and zero selected for both reads."""
    dut.write_valid_i.value = 0
    dut.write_index_i.value = 0
    dut.write_value_i.value = 0
    dut.read_index_a_i.value = 0
    dut.read_index_b_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await Timer(1, unit="ns")


async def write_gpr(dut, index: int, value: int) -> None:
    """Present one architectural write for a rising edge."""
    dut.write_valid_i.value = 1
    dut.write_index_i.value = index
    dut.write_value_i.value = value
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")
    dut.write_valid_i.value = 0


async def read_pair(dut, index_a: int, index_b: int) -> tuple[int, int]:
    """Read both architectural ports after combinational propagation."""
    dut.read_index_a_i.value = index_a
    dut.read_index_b_i.value = index_b
    await Timer(1, unit="ns")
    return int(dut.read_value_a_o.value), int(dut.read_value_b_o.value)


@cocotb.test()
async def test_r5900_register_zero_reads_zero_and_ignores_writes(dut) -> None:
    """Return 128 zero bits before, during, and after every boundary-class write."""
    await start_clock(dut)
    assert await read_pair(dut, 0, 0) == (0, 0)

    for value in (0, 1, 1 << 127, GPR_MASK, 0xAAAA_5555_AAAA_5555_AAAA_5555_AAAA_5555):
        await write_gpr(dut, 0, value)
        assert await read_pair(dut, 0, 0) == (0, 0)


@cocotb.test()
async def test_r5900_register_zero_masks_snapshot_without_corrupting_other_gprs(dut) -> None:
    """Preserve all writable GPRs while forcing packed lane zero to 128 zero bits."""
    await start_clock(dut)
    expected = [0] + [register_value(index) for index in range(1, GPR_COUNT)]
    for index in range(1, GPR_COUNT):
        await write_gpr(dut, index, expected[index])

    preserved_index = 17
    await write_gpr(dut, 0, GPR_MASK)
    assert await read_pair(dut, 0, preserved_index) == (0, expected[preserved_index])
    assert await read_pair(dut, GPR_COUNT - 1, 0) == (expected[-1], 0)

    packed = sum(value << (index * GPR_WIDTH) for index, value in enumerate(expected))
    assert int(dut.state_o.value) == packed
