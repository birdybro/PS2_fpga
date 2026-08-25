"""Cocotb tests for the standalone functional R5900 program counter."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
PC_MASK = (1 << 32) - 1
INSTRUCTION_BYTES = 4
REDIRECT_PC = 0x89AB_CDEF
RESET_PRIORITY_PC = 0x4001


async def start_clock(dut) -> None:
    """Start the clock with all state-changing controls inactive."""
    dut.rst_ni.value = 1
    dut.start_pc_i.value = 0
    dut.advance_i.value = 0
    dut.redirect_valid_i.value = 0
    dut.redirect_pc_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await Timer(1, unit="ns")


async def edge(dut) -> None:
    """Advance one rising edge and allow the nonblocking update to settle."""
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut, start_pc: int) -> None:
    """Load one externally supplied simulation entry point synchronously."""
    dut.start_pc_i.value = start_pc
    dut.rst_ni.value = 0
    await edge(dut)
    dut.rst_ni.value = 1


@cocotb.test()
async def test_r5900_pc_loads_full_width_simulation_start_address(dut) -> None:
    """Preserve aligned and unaligned boundary starts without invented masking."""
    await start_clock(dut)
    for start_pc in (0, 1, 0x0010_0000, PC_MASK - 3, PC_MASK):
        await initialize(dut, start_pc)
        assert int(dut.pc_o.value) == start_pc


@cocotb.test()
async def test_r5900_pc_holds_and_advances_modulo_32_bits(dut) -> None:
    """Hold when disabled and wrap exact four-byte sequential increments."""
    await start_clock(dut)
    await initialize(dut, PC_MASK - 3)

    for _ in range(3):
        await edge(dut)
        assert int(dut.pc_o.value) == PC_MASK - 3

    dut.advance_i.value = 1
    await edge(dut)
    assert int(dut.pc_o.value) == 0
    await edge(dut)
    assert int(dut.pc_o.value) == INSTRUCTION_BYTES


@cocotb.test()
async def test_r5900_pc_redirect_has_priority_over_advance(dut) -> None:
    """Select an exact redirect, including unaligned values, when both controls assert."""
    await start_clock(dut)
    await initialize(dut, 0x1000)

    dut.advance_i.value = 1
    dut.redirect_valid_i.value = 1
    dut.redirect_pc_i.value = REDIRECT_PC
    await edge(dut)
    assert int(dut.pc_o.value) == REDIRECT_PC

    dut.redirect_valid_i.value = 0
    await edge(dut)
    assert int(dut.pc_o.value) == (REDIRECT_PC + INSTRUCTION_BYTES) & PC_MASK


@cocotb.test()
async def test_r5900_pc_initialization_has_highest_priority_and_resamples_start(dut) -> None:
    """Reload the harness start on every asserted-reset edge despite other controls."""
    await start_clock(dut)
    await initialize(dut, 0x2000)
    dut.advance_i.value = 1
    dut.redirect_valid_i.value = 1
    dut.redirect_pc_i.value = 0x3000
    dut.start_pc_i.value = RESET_PRIORITY_PC
    dut.rst_ni.value = 0
    await edge(dut)
    assert int(dut.pc_o.value) == RESET_PRIORITY_PC

    dut.start_pc_i.value = PC_MASK
    await edge(dut)
    assert int(dut.pc_o.value) == PC_MASK
