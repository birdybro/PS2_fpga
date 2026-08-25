"""R5900 instruction-fetch integration stimulus for behavioral system RAM."""

import cocotb
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer

FIRST_PC = 0x20
FIRST_INSTRUCTION = 0x1234_5678
SECOND_PC = 0x24
SECOND_INSTRUCTION = 0x89AB_CDEF


def drive_initial_inputs(dut) -> None:
    """Drive every platform input, including an ignored external memory request."""
    dut.mem_req_valid_i.value = 1
    dut.mem_req_write_i.value = 1
    dut.mem_req_addr_i.value = 0
    dut.mem_req_size_i.value = 2
    dut.mem_req_wdata_i.value = int.from_bytes(bytes([0xCC] * 16), "little")
    dut.mem_req_wstrb_i.value = 0xF
    dut.mem_rsp_ready_i.value = 0
    dut.ee_run_i.value = 0
    dut.ee_start_pc_i.value = 0
    dut.ram_backdoor_write_i.value = 0
    dut.ram_backdoor_addr_i.value = 0
    dut.ram_backdoor_wdata_i.value = 0
    dut.pass_i.value = 0
    dut.fail_i.value = 0
    dut.fail_code_i.value = 0
    dut.ee_fetch_start_i.value = 1
    dut.ee_fetch_pc_i.value = FIRST_PC
    dut.ee_instruction_ready_i.value = 0
    dut.arch_event_valid_i.value = 0
    dut.arch_event_source_i.value = 0
    dut.arch_event_kind_i.value = 0
    dut.arch_event_pc_i.value = 0
    dut.arch_event_instruction_i.value = 0
    dut.arch_event_identifier_i.value = 0
    dut.arch_event_value_i.value = 0


def assert_fetch_reset_state(dut) -> None:
    """Require the composed fetch and transaction state to remain reset."""
    assert int(dut.ee_fetch_start_ready_o.value) == 0
    assert int(dut.ee_fetch_request_accepted_o.value) == 0
    assert int(dut.ee_fetch_response_accepted_o.value) == 0
    assert int(dut.ee_fetch_response_expected_o.value) == 0
    assert int(dut.ee_instruction_valid_o.value) == 0
    assert int(dut.ee_instruction_o.value) == 0
    assert int(dut.ee_fetch_error_o.value) == 0
    assert int(dut.mem_outstanding_o.value) == 0


async def wait_for_reset_release(dut) -> None:
    """Check reset rejection, then remove fetch start before the first active edge."""
    for _ in range(2):
        await RisingEdge(dut.clk_o)
        await ReadOnly()
        assert int(dut.rst_no.value) == 0
        assert_fetch_reset_state(dut)
        await Timer(1, unit="ps")

    await FallingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.rst_no.value) == 1
    assert int(dut.ee_fetch_start_ready_o.value) == 1
    await Timer(1, unit="ps")
    dut.ee_fetch_start_i.value = 0


async def write_word_backdoor(dut, address: int, value: int) -> None:
    """Populate one little-endian instruction word through byte writes."""
    for offset, byte_value in enumerate(value.to_bytes(4, "little")):
        dut.ram_backdoor_write_i.value = 1
        dut.ram_backdoor_addr_i.value = address + offset
        dut.ram_backdoor_wdata_i.value = byte_value
        await RisingEdge(dut.clk_o)
        await ReadOnly()
        assert int(dut.ram_backdoor_in_bounds_o.value) == 1
        assert int(dut.ram_backdoor_rdata_o.value) == byte_value
        assert int(dut.mem_outstanding_o.value) == 0
        await Timer(1, unit="ps")
    dut.ram_backdoor_write_i.value = 0


async def start_fetch(dut, pc: int) -> None:
    """Start one fetch and observe its request handshake exactly once."""
    assert int(dut.ee_fetch_start_ready_o.value) == 1
    dut.ee_fetch_pc_i.value = pc
    dut.ee_fetch_start_i.value = 1

    await RisingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.ee_fetch_request_accepted_o.value) == 1
    assert int(dut.ee_fetch_start_ready_o.value) == 0
    assert int(dut.mem_outstanding_o.value) == 0
    await Timer(1, unit="ps")
    dut.ee_fetch_start_i.value = 0

    await RisingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.ee_fetch_request_accepted_o.value) == 0
    assert int(dut.ee_fetch_start_ready_o.value) == 0
    assert int(dut.ee_fetch_response_expected_o.value) == 0
    assert int(dut.mem_outstanding_o.value) == 1
    await Timer(1, unit="ps")


async def expect_latency_two_response(dut, expected_instruction: int) -> None:
    """Check the registered request handoff and two-cycle RAM response latency."""
    await RisingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.ee_fetch_response_expected_o.value) == 1
    assert int(dut.mem_rsp_valid_o.value) == 0
    assert int(dut.ee_instruction_valid_o.value) == 0
    assert int(dut.ee_fetch_start_ready_o.value) == 0
    await Timer(1, unit="ps")

    await RisingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.mem_rsp_valid_o.value) == 1
    assert int(dut.ee_fetch_response_accepted_o.value) == 1
    assert int(dut.ee_instruction_valid_o.value) == 0
    assert int(dut.ee_fetch_start_ready_o.value) == 0
    await Timer(1, unit="ps")

    await RisingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.mem_rsp_valid_o.value) == 0
    assert int(dut.ee_fetch_response_accepted_o.value) == 0
    assert int(dut.ee_fetch_response_expected_o.value) == 0
    assert int(dut.ee_instruction_valid_o.value) == 1
    assert int(dut.ee_instruction_o.value) == expected_instruction
    assert int(dut.ee_fetch_error_o.value) == 0
    assert int(dut.mem_outstanding_o.value) == 0
    await Timer(1, unit="ps")


async def hold_then_consume_instruction(dut, expected_instruction: int) -> None:
    """Hold the one-entry instruction buffer, then consume it cleanly."""
    for _ in range(3):
        assert int(dut.ee_fetch_start_ready_o.value) == 0
        await RisingEdge(dut.clk_o)
        await ReadOnly()
        assert int(dut.ee_instruction_valid_o.value) == 1
        assert int(dut.ee_instruction_o.value) == expected_instruction
        assert int(dut.ee_fetch_error_o.value) == 0
        await Timer(1, unit="ps")

    dut.ee_instruction_ready_i.value = 1
    await Timer(1, unit="ps")
    assert int(dut.ee_fetch_start_ready_o.value) == 1
    await RisingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.ee_instruction_valid_o.value) == 0
    assert int(dut.ee_fetch_start_ready_o.value) == 1
    await Timer(1, unit="ps")
    dut.ee_instruction_ready_i.value = 0


@cocotb.test()
async def fetch_reads_little_endian_words_with_latency_and_backpressure(dut) -> None:
    """Verify reset, memory ownership, latency, backpressure, and repeated fetches."""
    drive_initial_inputs(dut)
    await Timer(1, unit="ps")
    await wait_for_reset_release(dut)

    await write_word_backdoor(dut, FIRST_PC, FIRST_INSTRUCTION)
    await write_word_backdoor(dut, SECOND_PC, SECOND_INSTRUCTION)

    await start_fetch(dut, FIRST_PC)
    await expect_latency_two_response(dut, FIRST_INSTRUCTION)
    await hold_then_consume_instruction(dut, FIRST_INSTRUCTION)

    await start_fetch(dut, SECOND_PC)
    await expect_latency_two_response(dut, SECOND_INSTRUCTION)
    await hold_then_consume_instruction(dut, SECOND_INSTRUCTION)
