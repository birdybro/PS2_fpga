"""Directed code, priority, and one-shot tests for simulation FAIL state."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

FIRST_FAIL_CODE = 0x1234_5678
PRIORITY_FAIL_CODE = 0xA5A5_5A5A
LATER_FAIL_CODE = 0xFFFF_FFFF


async def sample_cycle(dut) -> tuple[int, int, int, int, int]:
    """Advance one edge and sample PASS/FAIL terminal state."""
    await RisingEdge(dut.clk_i)
    await ReadOnly()
    sample = (
        int(dut.pass_event_o.value),
        int(dut.pass_latched_o.value),
        int(dut.fail_event_o.value),
        int(dut.fail_latched_o.value),
        int(dut.fail_code_o.value),
    )
    await Timer(1, unit="ns")
    return sample


def drive_terminal_inputs(dut, *, passed: int, failed: int, code: int) -> None:
    """Drive one explicit terminal-request combination."""
    dut.pass_i.value = passed
    dut.fail_i.value = failed
    dut.fail_code_i.value = code


@cocotb.test()
async def fail_code_priority_and_first_terminal_result_are_stable(dut) -> None:
    """Capture one code, prioritize simultaneous FAIL, and reject later changes."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    dut.rst_ni.value = 0
    drive_terminal_inputs(dut, passed=1, failed=1, code=FIRST_FAIL_CODE)
    assert await sample_cycle(dut) == (0, 0, 0, 0, 0)

    dut.rst_ni.value = 1
    drive_terminal_inputs(dut, passed=0, failed=1, code=FIRST_FAIL_CODE)
    assert await sample_cycle(dut) == (0, 0, 1, 1, FIRST_FAIL_CODE)
    drive_terminal_inputs(dut, passed=1, failed=1, code=LATER_FAIL_CODE)
    assert await sample_cycle(dut) == (0, 0, 0, 1, FIRST_FAIL_CODE)

    dut.rst_ni.value = 0
    assert await sample_cycle(dut) == (0, 0, 0, 0, 0)
    dut.rst_ni.value = 1
    drive_terminal_inputs(dut, passed=1, failed=1, code=PRIORITY_FAIL_CODE)
    assert await sample_cycle(dut) == (0, 0, 1, 1, PRIORITY_FAIL_CODE)

    dut.rst_ni.value = 0
    assert await sample_cycle(dut) == (0, 0, 0, 0, 0)
    dut.rst_ni.value = 1
    drive_terminal_inputs(dut, passed=1, failed=0, code=0)
    assert await sample_cycle(dut) == (1, 1, 0, 0, 0)
    drive_terminal_inputs(dut, passed=0, failed=1, code=LATER_FAIL_CODE)
    assert await sample_cycle(dut) == (0, 1, 0, 0, 0)

    dut.rst_ni.value = 0
    assert await sample_cycle(dut) == (0, 0, 0, 0, 0)
    dut.rst_ni.value = 1
    drive_terminal_inputs(dut, passed=0, failed=1, code=FIRST_FAIL_CODE)
    assert await sample_cycle(dut) == (0, 0, 1, 1, FIRST_FAIL_CODE)
    drive_terminal_inputs(dut, passed=1, failed=0, code=0)
    assert await sample_cycle(dut) == (0, 0, 0, 1, FIRST_FAIL_CODE)
