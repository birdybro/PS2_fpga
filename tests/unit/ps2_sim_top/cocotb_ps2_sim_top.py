"""Reset and inactive-control integration tests for the simulation platform."""

import os

import cocotb
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer


def drive_reset_epoch_activity(dut) -> None:
    """Drive valid-looking activity that every reset-aware component must ignore."""
    dut.mem_req_valid_i.value = 1
    dut.mem_req_write_i.value = 0
    dut.mem_req_addr_i.value = 0
    dut.mem_req_size_i.value = 2
    dut.mem_req_wdata_i.value = 0
    dut.mem_req_wstrb_i.value = 0
    dut.mem_rsp_ready_i.value = 1
    dut.ee_fetch_start_i.value = 1
    dut.ee_fetch_pc_i.value = 0
    dut.ee_instruction_ready_i.value = 1
    dut.ram_backdoor_write_i.value = 0
    dut.ram_backdoor_addr_i.value = 0
    dut.ram_backdoor_wdata_i.value = 0
    dut.pass_i.value = 1
    dut.fail_i.value = 1
    dut.fail_code_i.value = 0xDEAD_0040
    dut.arch_event_valid_i.value = 1
    dut.arch_event_source_i.value = 1
    dut.arch_event_kind_i.value = 3
    dut.arch_event_pc_i.value = 0xBFC0_0000
    dut.arch_event_instruction_i.value = 0xFFFF_FFFF
    dut.arch_event_identifier_i.value = 0x0040
    dut.arch_event_value_i.value = (1 << 128) - 1


def drive_inactive_controls(dut) -> None:
    """Remove every request before the first active platform edge."""
    dut.mem_req_valid_i.value = 0
    dut.pass_i.value = 0
    dut.fail_i.value = 0
    dut.arch_event_valid_i.value = 0
    dut.ee_fetch_start_i.value = 0


def assert_reset_state(dut) -> None:
    """Check all reset-aware composed outputs after a reset edge."""
    assert int(dut.rst_no.value) == 0
    assert int(dut.mem_req_ready_o.value) == 0
    assert int(dut.mem_rsp_valid_o.value) == 0
    assert int(dut.mem_rsp_rdata_o.value) == 0
    assert int(dut.mem_rsp_error_o.value) == 0
    assert int(dut.mem_outstanding_o.value) == 0
    assert int(dut.ee_fetch_start_ready_o.value) == 0
    assert int(dut.ee_fetch_request_accepted_o.value) == 0
    assert int(dut.ee_fetch_response_accepted_o.value) == 0
    assert int(dut.ee_fetch_response_expected_o.value) == 0
    assert int(dut.ee_instruction_valid_o.value) == 0
    assert int(dut.ee_instruction_o.value) == 0
    assert int(dut.ee_fetch_error_o.value) == 0
    assert int(dut.timeout_o.value) == 0
    assert int(dut.cycle_count_o.value) == 0
    assert int(dut.pass_event_o.value) == 0
    assert int(dut.pass_latched_o.value) == 0
    assert int(dut.fail_event_o.value) == 0
    assert int(dut.fail_latched_o.value) == 0
    assert int(dut.fail_code_o.value) == 0


def assert_idle_active_state(dut) -> None:
    """Check the composed controls remain idle after reset releases."""
    assert int(dut.rst_no.value) == 1
    assert int(dut.mem_rsp_valid_o.value) == 0
    assert int(dut.mem_outstanding_o.value) == 0
    assert int(dut.ee_fetch_start_ready_o.value) == 0
    assert int(dut.ee_fetch_request_accepted_o.value) == 0
    assert int(dut.ee_fetch_response_accepted_o.value) == 0
    assert int(dut.ee_fetch_response_expected_o.value) == 0
    assert int(dut.ee_instruction_valid_o.value) == 0
    assert int(dut.ee_instruction_o.value) == 0
    assert int(dut.ee_fetch_error_o.value) == 0
    assert int(dut.timeout_o.value) == 0
    assert int(dut.cycle_count_o.value) == 0
    assert int(dut.pass_event_o.value) == 0
    assert int(dut.pass_latched_o.value) == 0
    assert int(dut.fail_event_o.value) == 0
    assert int(dut.fail_latched_o.value) == 0


@cocotb.test()
async def platform_composes_exact_reset_and_inactive_controls(dut) -> None:
    """Verify reset fanout, RAM gating, and post-reset idle integration."""
    reset_cycles = int(os.environ["SIM_RESET_CYCLES"])
    drive_reset_epoch_activity(dut)

    await Timer(1, unit="ps")
    assert int(dut.clk_o.value) == 0
    assert int(dut.rst_no.value) == 0

    for _ in range(reset_cycles):
        await RisingEdge(dut.clk_o)
        await ReadOnly()
        assert_reset_state(dut)
        await Timer(1, unit="ps")

    await FallingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.rst_no.value) == 1
    assert int(dut.mem_req_ready_o.value) == 1
    assert int(dut.ram_backdoor_in_bounds_o.value) == 1
    await Timer(1, unit="ps")

    drive_inactive_controls(dut)
    for _ in range(3):
        await RisingEdge(dut.clk_o)
        await ReadOnly()
        assert_idle_active_state(dut)
        await Timer(1, unit="ps")
