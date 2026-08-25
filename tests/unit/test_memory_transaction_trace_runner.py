"""Pytest orchestration for deterministic memory transaction tracing."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "memory_transaction_trace"
EXPECTED_TRACE = """# PS2_fpga memory transaction trace v1
cycle=00000002 kind=REQ write=0 addr=0x00001000 size=2 wdata=0x00000000000000000000000000000000 wstrb=0x0000
cycle=00000003 kind=REQ write=1 addr=0x00002000 size=4 wdata=0x0123456789abcdeffedcba9876543210 wstrb=0xffff
cycle=00000003 kind=RSP rdata=0x11112222333344445555666677778888 error=0
cycle=00000005 kind=RSP rdata=0xffff0000ffff0000aaaa5555aaaa5555 error=1
"""


@pytest.mark.unit
@pytest.mark.parametrize("trace_enabled", (False, True))
def test_memory_transaction_trace_with_verilator(trace_enabled: bool) -> None:
    """Require disabled silence or the exact enabled handshake trace."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    suffix = "enabled" if trace_enabled else "disabled"
    build_dir = build_root / "pytest" / f"memory_transaction_trace_{suffix}"
    results_path = build_root / "results" / f"cocotb-memory-transaction-trace-{suffix}.xml"
    trace_path = build_root / "traces" / f"memory-transactions-{suffix}.log"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.unlink(missing_ok=True)

    runner = get_runner("verilator")
    runner.build(
        sources=[
            REPO_ROOT / "rtl/memory/memory_bus_if.sv",
            REPO_ROOT / "sim/debug/memory_transaction_trace.sv",
            TESTBENCH_DIR / "memory_transaction_trace_top.sv",
        ],
        hdl_toplevel="memory_transaction_trace_top",
        parameters={"TRACE_ENABLE": int(trace_enabled)},
        build_args=["-Wall", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_memory_transaction_trace",
        hdl_toplevel="memory_transaction_trace_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        plusargs=[f"+MEM_TRACE_FILE={trace_path}"],
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
    if trace_enabled:
        assert trace_path.read_text(encoding="utf-8") == EXPECTED_TRACE
    else:
        assert not trace_path.exists()
