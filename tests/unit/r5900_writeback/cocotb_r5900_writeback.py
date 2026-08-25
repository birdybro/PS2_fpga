"""Directed tests for the centralized R5900 architectural writeback path."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
GPR_MASK = (1 << 128) - 1


async def edge(dut) -> None:
    """Advance one rising edge and allow register and combinational outputs to settle."""
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut) -> None:
    """Reset writeback control without assuming physical GPR reset contents."""
    dut.rst_ni.value = 0
    dut.commit_i.value = 0
    dut.destination_i.value = 0
    dut.value_i.value = 0
    dut.read_index_a_i.value = 0
    dut.read_index_b_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1


async def commit_once(dut, destination: int, value: int) -> None:
    """Assert one commit episode and sample its architectural write edge."""
    dut.destination_i.value = destination
    dut.value_i.value = value
    dut.commit_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.commit_accepted_o.value) == 1
    expected_write = destination != 0
    assert int(dut.writeback_valid_o.value) == expected_write
    assert int(dut.gpr_write_enable_o.value) == expected_write
    if expected_write:
        assert int(dut.writeback_destination_o.value) == destination
        assert int(dut.writeback_value_o.value) == value
        assert int(dut.gpr_write_index_o.value) == destination
        assert int(dut.gpr_write_data_o.value) == value
    await edge(dut)
    assert int(dut.commit_accepted_o.value) == 0
    assert int(dut.writeback_valid_o.value) == 0
    assert int(dut.gpr_write_enable_o.value) == 0
    dut.commit_i.value = 0
    await edge(dut)


async def read_gpr(dut, index: int, port: str = "a") -> int:
    """Read one initialized architectural GPR through the selected port."""
    getattr(dut, f"read_index_{port}_i").value = index
    await Timer(1, unit="ns")
    return int(getattr(dut, f"read_data_{port}_o").value)


@cocotb.test()
async def test_r5900_writeback_commits_exact_destination_and_value(dut) -> None:
    """Write full-width asymmetric boundaries through both architectural read ports."""
    await initialize(dut)
    cases = (
        (1, 0),
        (2, 1),
        (17, 1 << 127),
        (31, GPR_MASK),
        (5, 0x0123_4567_89AB_CDEF_FEDC_BA98_7654_3210),
    )
    for destination, value in cases:
        await commit_once(dut, destination, value)
        assert await read_gpr(dut, destination, "a") == value
        assert await read_gpr(dut, destination, "b") == value


@cocotb.test()
async def test_r5900_writeback_accepts_but_suppresses_gpr_zero(dut) -> None:
    """Consume a zero-destination attempt without an event, port write, or corruption."""
    await initialize(dut)
    baseline = 0xAAAA_5555_AAAA_5555_0123_4567_89AB_CDEF
    await commit_once(dut, 1, baseline)
    await commit_once(dut, 0, GPR_MASK)
    assert await read_gpr(dut, 0) == 0
    assert await read_gpr(dut, 1) == baseline


@cocotb.test()
async def test_r5900_writeback_is_one_shot_until_commit_rearms(dut) -> None:
    """Ignore held-high payload changes until a sampled low cycle rearms the path."""
    await initialize(dut)
    baseline = 0x1111_2222_3333_4444_5555_6666_7777_8888
    first_value = 0x8888_7777_6666_5555_4444_3333_2222_1111
    second_value = GPR_MASK
    await commit_once(dut, 6, baseline)

    dut.destination_i.value = 5
    dut.value_i.value = first_value
    dut.commit_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.commit_accepted_o.value) == 1
    await edge(dut)
    assert await read_gpr(dut, 5) == first_value

    dut.destination_i.value = 6
    dut.value_i.value = second_value
    for _ in range(3):
        await edge(dut)
        assert int(dut.commit_accepted_o.value) == 0
        assert int(dut.gpr_write_enable_o.value) == 0
        assert await read_gpr(dut, 6) == baseline

    dut.commit_i.value = 0
    await edge(dut)
    await commit_once(dut, 6, second_value)
    assert await read_gpr(dut, 6) == second_value


@cocotb.test()
async def test_r5900_writeback_reset_blocks_commit_and_rearms(dut) -> None:
    """Give reset priority over a commit while allowing the first post-reset edge."""
    await initialize(dut)
    dut.rst_ni.value = 0
    dut.commit_i.value = 1
    dut.destination_i.value = 7
    dut.value_i.value = GPR_MASK
    await Timer(1, unit="ns")
    assert int(dut.commit_accepted_o.value) == 0
    assert int(dut.gpr_write_enable_o.value) == 0
    await edge(dut)
    dut.rst_ni.value = 1
    await Timer(1, unit="ns")
    assert int(dut.commit_accepted_o.value) == 1
    assert int(dut.gpr_write_enable_o.value) == 1
    await edge(dut)
    assert await read_gpr(dut, 7) == GPR_MASK
