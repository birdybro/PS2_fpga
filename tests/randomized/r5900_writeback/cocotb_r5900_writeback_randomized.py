"""Deterministic randomized verification for R5900 architectural writeback."""

import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
GPR_COUNT = 32
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
RANDOM_CYCLES = 512


async def edge(dut) -> None:
    """Advance one rising edge and settle architectural state."""
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


def pack_gprs(gprs: list[int]) -> int:
    """Pack the independent model using the RTL's documented ascending index lanes."""
    return sum(value << (index * GPR_WIDTH) for index, value in enumerate(gprs))


@cocotb.test()
async def test_r5900_writeback_randomized(dut) -> None:
    """Compare one-shot commits and the full GPR snapshot to an independent model."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    generator = random.Random(seed)
    dut.rst_ni.value = 0
    dut.commit_i.value = 0
    dut.destination_i.value = 0
    dut.value_i.value = 0
    dut.read_index_a_i.value = 0
    dut.read_index_b_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1

    model = [0] * GPR_COUNT
    for destination in range(1, GPR_COUNT):
        value = generator.getrandbits(GPR_WIDTH)
        dut.destination_i.value = destination
        dut.value_i.value = value
        dut.commit_i.value = 1
        await edge(dut)
        model[destination] = value
        dut.commit_i.value = 0
        await edge(dut)
    assert int(dut.gprs_o.value) == pack_gprs(model)

    commit_seen = False
    for iteration in range(RANDOM_CYCLES):
        commit = bool(generator.getrandbits(1))
        destination = generator.randrange(GPR_COUNT)
        value = generator.getrandbits(GPR_WIDTH)
        dut.commit_i.value = commit
        dut.destination_i.value = destination
        dut.value_i.value = value
        await Timer(1, unit="ns")

        accepted = commit and not commit_seen
        write_valid = accepted and destination != 0
        assert int(dut.commit_accepted_o.value) == accepted, (
            f"seed={seed} iteration={iteration} accepted mismatch"
        )
        assert int(dut.writeback_valid_o.value) == write_valid, (
            f"seed={seed} iteration={iteration} valid mismatch"
        )
        if write_valid:
            assert int(dut.writeback_destination_o.value) == destination
            assert int(dut.writeback_value_o.value) == value

        await edge(dut)
        if write_valid:
            model[destination] = value & GPR_MASK
        model[0] = 0
        commit_seen = commit
        actual_gprs = int(dut.gprs_o.value)
        expected_gprs = pack_gprs(model)
        assert actual_gprs == expected_gprs, (
            f"seed={seed} iteration={iteration} destination={destination} "
            f"expected=0x{expected_gprs:x} actual=0x{actual_gprs:x}"
        )
