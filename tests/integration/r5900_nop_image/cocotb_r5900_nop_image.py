"""Sequential NOP image stimulus for the composed multi-cycle R5900 core."""

import cocotb
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer

START_PC = 0x20
NOP_COUNT = 4
MAX_CYCLES = 96
STATE_FETCH_REQUEST = 0
STATE_FETCH_RESPONSE = 1
STATE_DECODE = 2
STATE_EXECUTE = 3
STATE_WRITEBACK = 4
EXPECTED_COMPRESSED_STATES = [
    STATE_FETCH_REQUEST,
    STATE_FETCH_RESPONSE,
    STATE_DECODE,
    STATE_EXECUTE,
    STATE_WRITEBACK,
] * NOP_COUNT


def drive_initial_inputs(dut) -> None:
    """Hold the core before loading RAM and idle every unrelated harness input."""
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
    dut.ee_start_pc_i.value = START_PC
    dut.ee_fetch_start_i.value = 0
    dut.ee_fetch_pc_i.value = 0
    dut.ee_instruction_ready_i.value = 0
    dut.arch_event_valid_i.value = 0
    dut.arch_event_source_i.value = 0
    dut.arch_event_kind_i.value = 0
    dut.arch_event_pc_i.value = 0
    dut.arch_event_instruction_i.value = 0
    dut.arch_event_identifier_i.value = 0
    dut.arch_event_value_i.value = 0


async def wait_for_reset_release(dut) -> None:
    """Require the start PC and fetch-request state throughout reset."""
    for _ in range(2):
        await RisingEdge(dut.clk_o)
        await ReadOnly()
        assert int(dut.rst_no.value) == 0
        assert int(dut.ee_control_state_o.value) == STATE_FETCH_REQUEST
        assert int(dut.ee_pc_o.value) == START_PC
        assert int(dut.ee_fetch_start_ready_o.value) == 0
        assert int(dut.ee_retirement_valid_o.value) == 0
        assert int(dut.mem_outstanding_o.value) == 0
        await Timer(1, unit="ps")

    await FallingEdge(dut.clk_o)
    await ReadOnly()
    assert int(dut.rst_no.value) == 1
    assert int(dut.ee_control_state_o.value) == STATE_FETCH_REQUEST
    assert int(dut.ee_pc_o.value) == START_PC
    assert int(dut.ee_fetch_start_ready_o.value) == 0
    await Timer(1, unit="ps")


async def load_nop_image(dut) -> None:
    """Write the bounded all-zero instruction image while the core is held."""
    for address in range(START_PC, START_PC + (4 * NOP_COUNT)):
        dut.ram_backdoor_write_i.value = 1
        dut.ram_backdoor_addr_i.value = address
        dut.ram_backdoor_wdata_i.value = 0
        await RisingEdge(dut.clk_o)
        await ReadOnly()
        assert int(dut.ram_backdoor_in_bounds_o.value) == 1
        assert int(dut.ram_backdoor_rdata_o.value) == 0
        assert int(dut.ee_control_state_o.value) == STATE_FETCH_REQUEST
        assert int(dut.ee_pc_o.value) == START_PC
        assert int(dut.mem_outstanding_o.value) == 0
        await Timer(1, unit="ps")
    dut.ram_backdoor_write_i.value = 0


def compress_states(states: list[int]) -> list[int]:
    """Remove repeated wait states while preserving architectural ordering."""
    compressed: list[int] = []
    for state in states:
        if not compressed or compressed[-1] != state:
            compressed.append(state)
    return compressed


async def assert_halted_after_image(dut) -> None:
    """Require the held core to preserve the first PC beyond the image."""
    for _ in range(4):
        await RisingEdge(dut.clk_o)
        await ReadOnly()
        assert int(dut.ee_control_state_o.value) == STATE_FETCH_REQUEST
        assert int(dut.ee_pc_o.value) == START_PC + (4 * NOP_COUNT)
        assert int(dut.ee_retirement_valid_o.value) == 0
        assert int(dut.ee_fetch_start_ready_o.value) == 0
        assert int(dut.mem_outstanding_o.value) == 0
        assert int(dut.timeout_o.value) == 0
        await Timer(1, unit="ps")


@cocotb.test()
async def four_nops_fetch_decode_execute_and_retire_in_order(dut) -> None:
    """Verify ordered multi-cycle state, PC, transaction, and retirement behavior."""
    drive_initial_inputs(dut)
    await Timer(1, unit="ps")
    await wait_for_reset_release(dut)
    await load_nop_image(dut)

    dut.ee_run_i.value = 1
    await Timer(1, unit="ps")
    assert int(dut.ee_fetch_start_ready_o.value) == 1

    states: list[int] = [int(dut.ee_control_state_o.value)]
    retirements: list[tuple[int, int]] = []
    request_count = 0
    response_count = 0

    for _ in range(64):
        await RisingEdge(dut.clk_o)
        await ReadOnly()
        state = int(dut.ee_control_state_o.value)
        states.append(state)
        request_count += int(dut.ee_fetch_request_accepted_o.value)
        response_count += int(dut.ee_fetch_response_accepted_o.value)

        assert int(dut.timeout_o.value) == 0
        assert int(dut.ee_fetch_error_o.value) == 0
        assert int(dut.ee_reserved_valid_o.value) == 0
        assert int(dut.ee_writeback_valid_o.value) == 0

        if int(dut.ee_retirement_valid_o.value):
            assert state == STATE_WRITEBACK
            retirements.append(
                (
                    int(dut.ee_retirement_pc_o.value),
                    int(dut.ee_retirement_instruction_o.value),
                )
            )
            if len(retirements) == NOP_COUNT:
                await Timer(1, unit="ps")
                dut.ee_run_i.value = 0
                break

        await Timer(1, unit="ps")
    else:
        raise AssertionError("four NOPs did not retire within 64 active core cycles")

    assert retirements == [(START_PC + (4 * index), 0) for index in range(NOP_COUNT)]
    assert request_count == NOP_COUNT
    assert response_count == NOP_COUNT
    assert compress_states(states) == EXPECTED_COMPRESSED_STATES
    assert int(dut.ee_gprs_o.value) & ((1 << 128) - 1) == 0
    assert int(dut.cycle_count_o.value) < MAX_CYCLES
    assert int(dut.timeout_o.value) == 0
    await assert_halted_after_image(dut)
