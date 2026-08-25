"""Generated arithmetic EE ELF stimulus for the composed R5900 core."""

import os

import cocotb
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer

PROGRAM_WORDS = (
    0x3C01_1234,
    0x3421_5678,
    0x2402_FFFF,
    0x3823_FFFF,
    0x3064_00FF,
    0x0024_2821,
    0x0081_3023,
    0x00C0_382A,
    0x00C0_402B,
    0x28C9_0000,
    0x2C0A_FFFF,
    0x0024_5827,
    0x0000_0000,
)
WRITEBACK_DESTINATIONS = (1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, None)
WRITEBACK_LOW64 = (
    0x0000_0000_1234_0000,
    0x0000_0000_1234_5678,
    0xFFFF_FFFF_FFFF_FFFF,
    0x0000_0000_1234_A987,
    0x0000_0000_0000_0087,
    0x0000_0000_1234_56FF,
    0xFFFF_FFFF_EDCB_AA0F,
    0x0000_0000_0000_0001,
    0x0000_0000_0000_0000,
    0x0000_0000_0000_0001,
    0x0000_0000_0000_0001,
    0xFFFF_FFFF_EDCB_A900,
    None,
)
FINAL_LOW64 = {
    1: 0x0000_0000_1234_5678,
    2: 0xFFFF_FFFF_FFFF_FFFF,
    3: 0x0000_0000_1234_A987,
    4: 0x0000_0000_0000_0087,
    5: 0x0000_0000_1234_56FF,
    6: 0xFFFF_FFFF_EDCB_AA0F,
    7: 0x0000_0000_0000_0001,
    8: 0x0000_0000_0000_0000,
    9: 0x0000_0000_0000_0001,
    10: 0x0000_0000_0000_0001,
    11: 0xFFFF_FFFF_EDCB_A900,
}
MASK64 = (1 << 64) - 1
MASK128 = (1 << 128) - 1
STATE_FETCH_REQUEST = 0


def drive_initial_inputs(dut, entry_point: int) -> None:
    """Hold the core at the ELF entry while all unrelated controls are idle."""
    dut.mem_req_valid_i.value = 0
    dut.mem_req_write_i.value = 0
    dut.mem_req_addr_i.value = 0
    dut.mem_req_size_i.value = 0
    dut.mem_req_wdata_i.value = 0
    dut.mem_req_wstrb_i.value = 0
    dut.mem_rsp_ready_i.value = 0
    dut.ram_backdoor_write_i.value = 0
    dut.ram_backdoor_addr_i.value = 0
    dut.ram_backdoor_wdata_i.value = 0
    dut.pass_i.value = 0
    dut.fail_i.value = 0
    dut.fail_code_i.value = 0
    dut.ee_run_i.value = 0
    dut.ee_start_pc_i.value = entry_point
    dut.ee_fetch_start_i.value = 0
    dut.ee_fetch_pc_i.value = 0
    dut.ee_instruction_ready_i.value = 0
    dut.arch_event_valid_i.value = 1
    dut.arch_event_source_i.value = 0xFF
    dut.arch_event_kind_i.value = 0xFF
    dut.arch_event_pc_i.value = 0xDEAD_0000
    dut.arch_event_instruction_i.value = 0xFFFF_FFFF
    dut.arch_event_identifier_i.value = 0xFFFF
    dut.arch_event_value_i.value = MASK128


async def wait_for_reset_release(dut, entry_point: int) -> None:
    """Require exact ELF entry sampling during reset and a held core afterward."""
    for _ in range(2):
        await RisingEdge(dut.clk_o)
        await ReadOnly()
        assert int(dut.rst_no.value) == 0
        assert int(dut.ee_pc_o.value) == entry_point
        assert int(dut.ee_control_state_o.value) == STATE_FETCH_REQUEST
        assert int(dut.ee_fetch_start_ready_o.value) == 0
        await Timer(1, unit="ps")

    await FallingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.rst_no.value) == 1
    assert int(dut.ee_pc_o.value) == entry_point
    await Timer(1, unit="ps")


async def load_segment(dut, start_address: int, payload: bytes) -> None:
    """Copy exactly the loader-selected PT_LOAD memory range into RAM."""
    for offset, byte_value in enumerate(payload):
        dut.ram_backdoor_write_i.value = 1
        dut.ram_backdoor_addr_i.value = start_address + offset
        dut.ram_backdoor_wdata_i.value = byte_value
        await RisingEdge(dut.clk_o)
        await ReadOnly()
        assert int(dut.ram_backdoor_in_bounds_o.value) == 1
        assert int(dut.ram_backdoor_rdata_o.value) == byte_value
        assert int(dut.mem_outstanding_o.value) == 0
        await Timer(1, unit="ps")
    dut.ram_backdoor_write_i.value = 0


def extract_gpr(packed_gprs: int, index: int) -> int:
    """Extract one 128-bit element from the packed ascending architectural view."""
    return (packed_gprs >> (128 * index)) & MASK128


def assert_final_gprs(packed_gprs: int, initial_gprs: int) -> None:
    """Check final scalar results, preserved upper lanes, zero, and skipped prefix."""
    assert extract_gpr(packed_gprs, 0) == 0
    for index, expected_low64 in FINAL_LOW64.items():
        actual = extract_gpr(packed_gprs, index)
        initial = extract_gpr(initial_gprs, index)
        assert actual & MASK64 == expected_low64
        assert actual >> 64 == initial >> 64
    assert extract_gpr(packed_gprs, 12) == extract_gpr(initial_gprs, 12)


async def pulse_pass(dut) -> None:
    """Emit and retain the simulator's deterministic success condition."""
    dut.pass_i.value = 1
    await RisingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.pass_event_o.value) == 1
    assert int(dut.pass_latched_o.value) == 1
    await Timer(1, unit="ps")
    dut.pass_i.value = 0
    await RisingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.pass_event_o.value) == 0
    assert int(dut.pass_latched_o.value) == 1
    await Timer(1, unit="ps")


async def execute_program(dut, entry_point: int) -> tuple[int, int]:
    """Run until the complete expected retirement and writeback stream is observed."""
    retirement_index = 0
    request_count = 0
    response_count = 0
    for _ in range(128):
        await RisingEdge(dut.clk_o)
        await ReadOnly()
        request_count += int(dut.ee_fetch_request_accepted_o.value)
        response_count += int(dut.ee_fetch_response_accepted_o.value)
        assert int(dut.timeout_o.value) == 0
        assert int(dut.ee_fetch_error_o.value) == 0
        assert int(dut.ee_reserved_valid_o.value) == 0

        if int(dut.ee_retirement_valid_o.value):
            expected_word = PROGRAM_WORDS[retirement_index]
            assert int(dut.ee_retirement_pc_o.value) == entry_point + (4 * retirement_index)
            assert int(dut.ee_retirement_instruction_o.value) == expected_word
            expected_destination = WRITEBACK_DESTINATIONS[retirement_index]
            expected_low64 = WRITEBACK_LOW64[retirement_index]
            if expected_destination is None:
                assert int(dut.ee_writeback_valid_o.value) == 0
            else:
                assert int(dut.ee_writeback_valid_o.value) == 1
                assert int(dut.ee_writeback_destination_o.value) == expected_destination
                assert int(dut.ee_writeback_value_o.value) & MASK64 == expected_low64
            retirement_index += 1
            if retirement_index == len(PROGRAM_WORDS):
                await Timer(1, unit="ps")
                dut.ee_run_i.value = 0
                return request_count, response_count

        await Timer(1, unit="ps")
    raise AssertionError("arithmetic ELF did not retire before the execution bound")


@cocotb.test()
async def elf_entry_executes_arithmetic_and_reaches_pass(dut) -> None:
    """Execute the loaded stream and compare retirement, writeback, GPR, and PASS."""
    entry_point = int(os.environ["SIM_ENTRY_POINT"])
    program_end = int(os.environ["SIM_PROGRAM_END"])
    segment_start = int(os.environ["SIM_SEGMENT_START"])
    segment_end = int(os.environ["SIM_SEGMENT_END"])
    memory_image = bytes.fromhex(os.environ["SIM_MEMORY_IMAGE_HEX"])
    segment_payload = memory_image[segment_start:segment_end]

    drive_initial_inputs(dut, entry_point)
    await Timer(1, unit="ps")
    await wait_for_reset_release(dut, entry_point)
    await load_segment(dut, segment_start, segment_payload)
    initial_gprs = int(dut.ee_gprs_o.value)

    dut.ee_run_i.value = 1
    await Timer(1, unit="ps")
    assert int(dut.ee_fetch_start_ready_o.value) == 1

    request_count, response_count = await execute_program(dut, entry_point)
    assert request_count == len(PROGRAM_WORDS)
    assert response_count == len(PROGRAM_WORDS)
    assert int(dut.ee_pc_o.value) == program_end
    assert_final_gprs(int(dut.ee_gprs_o.value), initial_gprs)

    await RisingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.ee_control_state_o.value) == STATE_FETCH_REQUEST
    assert int(dut.ee_pc_o.value) == program_end
    assert int(dut.mem_outstanding_o.value) == 0
    assert int(dut.timeout_o.value) == 0
    await Timer(1, unit="ps")

    await pulse_pass(dut)
