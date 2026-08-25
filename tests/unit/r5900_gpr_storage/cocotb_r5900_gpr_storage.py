"""Cocotb tests for reset-free two-read, one-write R5900 GPR storage."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

GPR_COUNT = 32
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
CLOCK_PERIOD_NS = 10


def register_value(index: int) -> int:
    """Return one asymmetric full-width value unique to a physical location."""
    return ((1 << 127) | (index << 96) | (index << 64) | (index << 32) | index) & GPR_MASK


async def start_clock(dut) -> None:
    """Start the storage clock and establish inactive write controls."""
    dut.write_valid_i.value = 0
    dut.write_index_i.value = 0
    dut.write_value_i.value = 0
    dut.read_index_a_i.value = 0
    dut.read_index_b_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await Timer(1, unit="ns")


async def write_gpr(dut, index: int, value: int) -> None:
    """Commit one physical storage write on the next rising edge."""
    dut.write_valid_i.value = 1
    dut.write_index_i.value = index
    dut.write_value_i.value = value
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")
    dut.write_valid_i.value = 0


async def read_pair(dut, index_a: int, index_b: int) -> tuple[int, int]:
    """Read two independent combinational ports after propagation."""
    dut.read_index_a_i.value = index_a
    dut.read_index_b_i.value = index_b
    await Timer(1, unit="ns")
    return int(dut.read_value_a_o.value), int(dut.read_value_b_o.value)


@cocotb.test()
async def test_r5900_storage_writes_and_reads_every_physical_register(dut) -> None:
    """Write all 32 locations, then verify both read ports and the packed snapshot."""
    await start_clock(dut)
    expected = [register_value(index) for index in range(GPR_COUNT)]
    for index, value in enumerate(expected):
        await write_gpr(dut, index, value)

    for index in range(0, GPR_COUNT, 2):
        assert await read_pair(dut, index, index + 1) == (expected[index], expected[index + 1])

    packed = sum(value << (index * GPR_WIDTH) for index, value in enumerate(expected))
    assert int(dut.state_o.value) == packed


@cocotb.test()
async def test_r5900_storage_holds_when_write_is_disabled(dut) -> None:
    """Preserve a location across disabled writes and unrelated clock edges."""
    await start_clock(dut)
    index = 13
    baseline = 0x0123_4567_89AB_CDEF_FEDC_BA98_7654_3210
    await write_gpr(dut, index, baseline)

    dut.write_valid_i.value = 0
    dut.write_index_i.value = index
    dut.write_value_i.value = GPR_MASK ^ baseline
    for _ in range(3):
        await RisingEdge(dut.clk_i)
    assert await read_pair(dut, index, index) == (baseline, baseline)


@cocotb.test()
async def test_r5900_storage_updates_only_after_write_edge(dut) -> None:
    """Expose the old value before an edge and the new value after that edge."""
    await start_clock(dut)
    index = 21
    old_value = 0xAAAA_5555_AAAA_5555_0123_4567_89AB_CDEF
    new_value = 0x5555_AAAA_5555_AAAA_FEDC_BA98_7654_3210
    await write_gpr(dut, index, old_value)

    dut.read_index_a_i.value = index
    dut.write_valid_i.value = 1
    dut.write_index_i.value = index
    dut.write_value_i.value = new_value
    await Timer(1, unit="ns")
    assert int(dut.read_value_a_o.value) == old_value

    await RisingEdge(dut.clk_i)
    await ReadOnly()
    assert int(dut.read_value_a_o.value) == new_value
