"""Directed architectural tests for the exact zero-word R5900 NOP."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 10
GPR_COUNT = 32
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1


async def edge(dut) -> None:
    """Advance one rising edge and settle architectural state."""
    await RisingEdge(dut.clk_i)
    await Timer(1, unit="ns")


async def initialize(dut, start_pc: int) -> None:
    """Start the clock and reset the functional execution harness."""
    dut.rst_ni.value = 0
    dut.start_pc_i.value = start_pc
    dut.instruction_valid_i.value = 0
    dut.instruction_i.value = 0
    dut.seed_commit_i.value = 0
    dut.seed_destination_i.value = 0
    dut.seed_value_i.value = 0
    dut.read_index_a_i.value = 0
    dut.read_index_b_i.value = 0
    cocotb.start_soon(Clock(dut.clk_i, CLOCK_PERIOD_NS, unit="ns").start())
    await edge(dut)
    dut.rst_ni.value = 1


async def reset_pc(dut, start_pc: int) -> None:
    """Reload a simulation start PC without changing physical GPR storage."""
    dut.instruction_valid_i.value = 0
    dut.seed_commit_i.value = 0
    dut.start_pc_i.value = start_pc
    dut.rst_ni.value = 0
    await edge(dut)
    dut.rst_ni.value = 1


async def seed_gpr(dut, destination: int, value: int) -> None:
    """Initialize one physical nonzero GPR through the architectural writeback path."""
    dut.seed_destination_i.value = destination
    dut.seed_value_i.value = value
    dut.seed_commit_i.value = 1
    await edge(dut)
    dut.seed_commit_i.value = 0
    await edge(dut)


async def execute_nop(dut) -> tuple[int, int]:
    """Check pre-edge NOP controls, execute one edge, and return old/new PCs."""
    old_pc = int(dut.pc_o.value)
    dut.instruction_i.value = 0
    dut.instruction_valid_i.value = 1
    await Timer(1, unit="ns")
    assert int(dut.execute_valid_o.value) == 1
    assert int(dut.operation_o.value) == 1
    assert int(dut.execute_complete_o.value) == 1
    assert int(dut.pc_advance_o.value) == 1
    assert int(dut.execute_writeback_commit_o.value) == 0
    assert int(dut.writeback_valid_o.value) == 0
    assert int(dut.retirement_valid_o.value) == 1
    assert int(dut.retirement_pc_o.value) == old_pc
    assert int(dut.retirement_instruction_o.value) == 0
    assert int(dut.reserved_valid_o.value) == 0
    await edge(dut)
    dut.instruction_valid_i.value = 0
    await Timer(1, unit="ns")
    assert int(dut.retirement_valid_o.value) == 0
    return old_pc, int(dut.pc_o.value)


@cocotb.test()
async def test_r5900_nop_advances_pc_and_emits_exact_retirement_trace(dut) -> None:
    """Advance by four with wrap while tracing the pre-advance PC and exact word."""
    await initialize(dut, 0)
    for start_pc in (0, 4, 0x0010_0000, 0xFFFF_FFFC):
        await reset_pc(dut, start_pc)
        old_pc, new_pc = await execute_nop(dut)
        assert old_pc == start_pc
        assert new_pc == (start_pc + 4) & 0xFFFF_FFFF


@cocotb.test()
async def test_r5900_nop_preserves_every_architectural_gpr(dut) -> None:
    """Preserve a fully initialized asymmetric 4,096-bit GPR snapshot."""
    await initialize(dut, 0x0010_0000)
    expected = [0] * GPR_COUNT
    for destination in range(1, GPR_COUNT):
        value = ((destination << 120) | (1 << (destination + 32)) | destination) & GPR_MASK
        await seed_gpr(dut, destination, value)
        expected[destination] = value
    packed = sum(value << (index * GPR_WIDTH) for index, value in enumerate(expected))
    assert int(dut.gprs_o.value) == packed

    await execute_nop(dut)
    assert int(dut.gprs_o.value) == packed


@cocotb.test()
async def test_r5900_nop_requires_exact_zero_word(dut) -> None:
    """Keep near-zero SPECIAL and unrelated primary encodings out of execution."""
    await initialize(dut, 0x1000)
    for instruction in (1, 0x20_0000, 0x20_0040, 0x3005_1234, 0xFFFF_FFFF):
        before_pc = int(dut.pc_o.value)
        dut.instruction_i.value = instruction
        dut.instruction_valid_i.value = 1
        await Timer(1, unit="ns")
        assert int(dut.execute_valid_o.value) == 0
        assert int(dut.execute_complete_o.value) == 0
        assert int(dut.pc_advance_o.value) == 0
        assert int(dut.execute_writeback_commit_o.value) == 0
        assert int(dut.retirement_valid_o.value) == 0
        assert int(dut.reserved_valid_o.value) == 1
        await edge(dut)
        dut.instruction_valid_i.value = 0
        await Timer(1, unit="ns")
        assert int(dut.pc_o.value) == before_pc
