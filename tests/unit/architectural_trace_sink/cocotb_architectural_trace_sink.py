"""Deterministic stimulus for the architectural event trace sink."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

GPR_VALUE = 0x0123_4567_89AB_CDEF_FEDC_BA98_7654_3210
EXCEPTION_VALUE = 0x0000_0000_0000_0000_0000_0000_8000_0180


def drive_idle(dut) -> None:
    """Drive known inactive values on the complete trace input record."""
    dut.event_valid_i.value = 0
    dut.event_source_i.value = 0
    dut.event_kind_i.value = 0
    dut.event_pc_i.value = 0
    dut.event_instruction_i.value = 0
    dut.event_identifier_i.value = 0
    dut.event_value_i.value = 0


async def cycle(dut) -> None:
    """Advance one edge after trace input state has settled."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    await Timer(1, unit="ns")


@cocotb.test()
async def trace_stimulus_covers_reset_gaps_and_payloads(dut) -> None:
    """Emit three records separated by reset and inactive cycles."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    drive_idle(dut)
    dut.rst_ni.value = 0
    dut.event_valid_i.value = 1
    await cycle(dut)

    dut.rst_ni.value = 1
    dut.event_valid_i.value = 0
    await cycle(dut)

    dut.event_valid_i.value = 1
    dut.event_source_i.value = 0x01
    dut.event_kind_i.value = 0x01
    dut.event_pc_i.value = 0x0010_0000
    dut.event_instruction_i.value = 0x0000_0000
    await cycle(dut)

    dut.event_kind_i.value = 0x02
    dut.event_pc_i.value = 0x0010_0004
    dut.event_instruction_i.value = 0x3405_1234
    dut.event_identifier_i.value = 0x0005
    dut.event_value_i.value = GPR_VALUE
    await cycle(dut)

    drive_idle(dut)
    await cycle(dut)

    dut.event_valid_i.value = 1
    dut.event_source_i.value = 0x01
    dut.event_kind_i.value = 0x03
    dut.event_pc_i.value = 0x8000_0180
    dut.event_instruction_i.value = 0x0000_000D
    dut.event_identifier_i.value = 0x000A
    dut.event_value_i.value = EXCEPTION_VALUE
    await cycle(dut)

    drive_idle(dut)
    await cycle(dut)
