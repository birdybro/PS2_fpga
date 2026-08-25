"""Raw-file loader and composed platform RAM integration stimulus."""

import os
from pathlib import Path

import cocotb
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer

READ_WINDOWS = (
    (0, 4),
    (28, 4),
    (32, 16),
    (40, 8),
    (48, 16),
    (64, 4),
    (112, 16),
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
    dut.ee_run_i.value = 0
    dut.ee_start_pc_i.value = 0
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
async def raw_file_image_reads_back_byte_exactly(dut) -> None:
    """Copy loader output into platform RAM and read every boundary window."""
    ram_size = int(os.environ["SIM_RAM_SIZE"])
    load_address = int(os.environ["SIM_LOAD_ADDRESS"])
    sentinel = int(os.environ["SIM_SENTINEL"])
    raw_payload = Path(os.environ["SIM_RAW_BINARY_PATH"]).read_bytes()
    memory_image = bytes.fromhex(os.environ["SIM_RAM_IMAGE_HEX"])

    expected_image = bytearray([sentinel] * ram_size)
    expected_image[load_address : load_address + len(raw_payload)] = raw_payload
    assert memory_image == expected_image

    drive_idle(dut)
    await wait_for_reset_release(dut)
    await copy_bytes_through_backdoor(dut, 0, bytes([sentinel] * ram_size))
    loaded_payload = memory_image[load_address : load_address + len(raw_payload)]
    await copy_bytes_through_backdoor(dut, load_address, loaded_payload)

    for address, size_bytes in READ_WINDOWS:
        expected = int.from_bytes(expected_image[address : address + size_bytes], "little")
        response = await read_transaction(dut, address, size_bytes)
        assert response == expected, (
            f"read mismatch address=0x{address:08x} size={size_bytes}: "
            f"expected=0x{expected:032x} actual=0x{response:032x}"
        )
