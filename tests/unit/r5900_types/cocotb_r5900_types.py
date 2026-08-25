"""Cocotb checks for R5900 package widths and debug-interface field mapping."""

import cocotb
from cocotb.triggers import Timer

GPR_COUNT = 32
GPR_WIDTH = 128
GPR_MASK = (1 << GPR_WIDTH) - 1
GPR_FILE_MASK = (1 << (GPR_COUNT * GPR_WIDTH)) - 1
TEST_PC = 0x89AB_CDEF
TEST_INSTRUCTION = 0x012A_4020
TEST_WRITEBACK = 0xFEDC_BA98_7654_3210_0123_4567_89AB_CDEF
TEST_RESERVED_PC = 0x1357_9BDF
TEST_RESERVED_INSTRUCTION = 0x2468_ACE0


async def settle() -> None:
    """Allow continuous assignments to propagate through the debug probe."""
    await Timer(1, unit="ns")


@cocotb.test()
async def test_r5900_debug_fields_preserve_boundary_values(dut) -> None:
    """Pass asymmetric maximum-width values through every typed interface field."""
    dut.pc_i.value = TEST_PC
    dut.gprs_i.value = GPR_FILE_MASK
    dut.instruction_i.value = TEST_INSTRUCTION
    dut.writeback_valid_i.value = 1
    dut.writeback_destination_i.value = GPR_COUNT - 1
    dut.writeback_value_i.value = TEST_WRITEBACK
    dut.reserved_valid_i.value = 1
    dut.reserved_pc_i.value = TEST_RESERVED_PC
    dut.reserved_instruction_i.value = TEST_RESERVED_INSTRUCTION

    await settle()

    assert int(dut.pc_o.value) == TEST_PC
    assert int(dut.gprs_o.value) == GPR_FILE_MASK
    assert int(dut.instruction_o.value) == TEST_INSTRUCTION
    assert int(dut.writeback_valid_o.value) == 1
    assert int(dut.writeback_destination_o.value) == GPR_COUNT - 1
    assert int(dut.writeback_value_o.value) == TEST_WRITEBACK
    assert int(dut.reserved_valid_o.value) == 1
    assert int(dut.reserved_pc_o.value) == TEST_RESERVED_PC
    assert int(dut.reserved_instruction_o.value) == TEST_RESERVED_INSTRUCTION


@cocotb.test()
async def test_r5900_gpr_file_uses_index_zero_in_low_packed_lane(dut) -> None:
    """Lock the packed debug mapping so Python and RTL agree on every GPR lane."""
    values = [((1 << 127) | (index << 64) | index) & GPR_MASK for index in range(GPR_COUNT)]
    packed = sum(value << (index * GPR_WIDTH) for index, value in enumerate(values))
    dut.gprs_i.value = packed

    await settle()

    assert int(dut.gprs_o.value) == packed
    assert int(dut.gpr_zero_o.value) == values[0]
    assert int(dut.gpr_last_o.value) == values[-1]
