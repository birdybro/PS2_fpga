"""EE ELF loader and composed platform RAM integration stimulus."""

import os
from pathlib import Path

import cocotb
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer

ENTRY_POINT = 0x44
FIRST_FILE_OFFSET = 0x100
FIRST_START = 0x40
FIRST_PAYLOAD = bytes.fromhex("10 32 54 76 98 ba dc fe 01 23 45 67 89 ab cd ef")
FIRST_END = 0x60
SECOND_FILE_OFFSET = 0x120
SECOND_START = 0xA0
SECOND_PAYLOAD = bytes.fromhex("ff ee dd cc bb aa 99 88")
SECOND_END = 0xB0
READ_WINDOWS = (
    (0x30, 16),
    (FIRST_START, 16),
    (ENTRY_POINT, 4),
    (0x50, 16),
    (FIRST_END, 16),
    (0x90, 16),
    (SECOND_START, 8),
    (SECOND_START, 16),
    (SECOND_END, 16),
    (0xF0, 16),
)
SIZE_ENCODING = {4: 2, 8: 3, 16: 4}


def drive_idle(dut) -> None:
    """Drive every simulation-platform input to a known inactive value."""
    dut.mem_req_valid_i.value = 0
    dut.mem_req_write_i.value = 0
    dut.mem_req_addr_i.value = 0
    dut.mem_req_size_i.value = 0
    dut.mem_req_wdata_i.value = 0
    dut.mem_req_wstrb_i.value = 0
    dut.mem_rsp_ready_i.value = 1
    dut.ee_fetch_start_i.value = 0
    dut.ee_fetch_pc_i.value = 0
    dut.ee_instruction_ready_i.value = 0
    dut.ram_backdoor_write_i.value = 0
    dut.ram_backdoor_addr_i.value = 0
    dut.ram_backdoor_wdata_i.value = 0
    dut.pass_i.value = 0
    dut.fail_i.value = 0
    dut.fail_code_i.value = 0
    dut.arch_event_valid_i.value = 0
    dut.arch_event_source_i.value = 0
    dut.arch_event_kind_i.value = 0
    dut.arch_event_pc_i.value = 0
    dut.arch_event_instruction_i.value = 0
    dut.arch_event_identifier_i.value = 0
    dut.arch_event_value_i.value = 0


async def wait_for_reset_release(dut) -> None:
    """Wait for the platform sequencer's falling-edge reset release."""
    while True:
        await FallingEdge(dut.clk_o)
        await ReadOnly()
        released = int(dut.rst_no.value) == 1
        await Timer(1, unit="ps")
        if released:
            return


async def copy_bytes_through_backdoor(dut, start_address: int, payload: bytes) -> None:
    """Copy one explicit byte range into behavioral RAM on active edges."""
    for address, value in enumerate(payload, start=start_address):
        dut.ram_backdoor_write_i.value = 1
        dut.ram_backdoor_addr_i.value = address
        dut.ram_backdoor_wdata_i.value = value
        await RisingEdge(dut.clk_o)
        await ReadOnly()
        assert int(dut.ram_backdoor_in_bounds_o.value) == 1
        assert int(dut.ram_backdoor_rdata_o.value) == value
        await Timer(1, unit="ps")
    dut.ram_backdoor_write_i.value = 0


async def read_transaction(dut, address: int, size_bytes: int) -> int:
    """Issue one aligned read and return its complete 128-bit response payload."""
    dut.mem_req_valid_i.value = 1
    dut.mem_req_write_i.value = 0
    dut.mem_req_addr_i.value = address
    dut.mem_req_size_i.value = SIZE_ENCODING[size_bytes]
    await Timer(1, unit="ps")
    assert int(dut.mem_req_ready_o.value) == 1

    await RisingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.mem_rsp_valid_o.value) == 1
    assert int(dut.mem_rsp_error_o.value) == 0
    assert int(dut.mem_outstanding_o.value) == 1
    response = int(dut.mem_rsp_rdata_o.value)
    await Timer(1, unit="ps")

    dut.mem_req_valid_i.value = 0
    await RisingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.mem_rsp_valid_o.value) == 0
    assert int(dut.mem_outstanding_o.value) == 0
    await Timer(1, unit="ps")
    return response


@cocotb.test()
async def ee_elf_segments_bss_and_entry_read_back_exactly(dut) -> None:
    """Overlay loader-selected segments and verify file, BSS, gap, and entry bytes."""
    ram_size = int(os.environ["SIM_RAM_SIZE"])
    sentinel = int(os.environ["SIM_SENTINEL"])
    entry_point = int(os.environ["SIM_ENTRY_POINT"])
    memory_image = bytes.fromhex(os.environ["SIM_RAM_IMAGE_HEX"])
    elf_image = Path(os.environ["SIM_ELF_PATH"]).read_bytes()
    segment_ranges = tuple(
        tuple(int(value) for value in encoded_range.split(":"))
        for encoded_range in os.environ["SIM_SEGMENT_RANGES"].split(",")
    )

    assert entry_point == ENTRY_POINT
    assert segment_ranges == ((FIRST_START, FIRST_END), (SECOND_START, SECOND_END))
    assert elf_image[FIRST_FILE_OFFSET : FIRST_FILE_OFFSET + len(FIRST_PAYLOAD)] == FIRST_PAYLOAD
    assert (
        elf_image[SECOND_FILE_OFFSET : SECOND_FILE_OFFSET + len(SECOND_PAYLOAD)] == SECOND_PAYLOAD
    )

    expected_image = bytearray([sentinel] * ram_size)
    expected_image[FIRST_START : FIRST_START + len(FIRST_PAYLOAD)] = FIRST_PAYLOAD
    expected_image[FIRST_START + len(FIRST_PAYLOAD) : FIRST_END] = bytes(
        FIRST_END - FIRST_START - len(FIRST_PAYLOAD)
    )
    expected_image[SECOND_START : SECOND_START + len(SECOND_PAYLOAD)] = SECOND_PAYLOAD
    expected_image[SECOND_START + len(SECOND_PAYLOAD) : SECOND_END] = bytes(
        SECOND_END - SECOND_START - len(SECOND_PAYLOAD)
    )
    assert memory_image == expected_image

    drive_idle(dut)
    await wait_for_reset_release(dut)
    await copy_bytes_through_backdoor(dut, 0, bytes([sentinel] * ram_size))
    for start_address, end_address in segment_ranges:
        await copy_bytes_through_backdoor(
            dut,
            start_address,
            memory_image[start_address:end_address],
        )

    for address, size_bytes in READ_WINDOWS:
        expected = int.from_bytes(expected_image[address : address + size_bytes], "little")
        response = await read_transaction(dut, address, size_bytes)
        assert response == expected, (
            f"read mismatch address=0x{address:08x} size={size_bytes}: "
            f"expected=0x{expected:032x} actual=0x{response:032x}"
        )
