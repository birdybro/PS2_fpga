"""Pytest orchestration for memory bus protocol assertion tests."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "memory_bus_protocol"
VIOLATIONS = (
    "unsupported_size",
    "request_stability",
    "request_withdrawal",
    "response_stability",
    "response_withdrawal",
    "response_causality",
    "single_outstanding",
)
VIOLATION_MARKERS = {
    "unsupported_size": "MEMBUS_SIZE",
    "request_stability": "MEMBUS_REQ_STABLE",
    "request_withdrawal": "MEMBUS_REQ_VALID",
    "response_stability": "MEMBUS_RSP_STABLE",
    "response_withdrawal": "MEMBUS_RSP_VALID",
    "response_causality": "MEMBUS_RSP_CAUSAL",
    "single_outstanding": "MEMBUS_OUTSTANDING",
}


@pytest.fixture(scope="module")
def protocol_checker_build() -> tuple:
    """Build one assertion-enabled executable shared by all protocol cases."""
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "memory_bus_protocol"
    runner = get_runner("verilator")
    runner.build(
        sources=[
            REPO_ROOT / "rtl/memory/memory_bus_if.sv",
            REPO_ROOT / "rtl/memory/memory_bus_protocol_checker.sv",
            TESTBENCH_DIR / "memory_bus_protocol_top.sv",
        ],
        hdl_toplevel="memory_bus_protocol_top",
        build_args=["-Wall", "--assert", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    return runner, build_dir, build_root


@pytest.mark.unit
def test_memory_bus_protocol_accepts_legal_traffic(protocol_checker_build: tuple) -> None:
    """Run stalls, every size, zero latency, and response/request replacement."""
    runner, build_dir, build_root = protocol_checker_build
    results_path = build_root / "results" / "cocotb-memory-bus-protocol-valid.xml"
    result = runner.test(
        test_module="cocotb_memory_bus_protocol_valid",
        hdl_toplevel="memory_bus_protocol_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=int(os.environ.get("RANDOM_SEED", "1")),
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")


@pytest.mark.unit
@pytest.mark.parametrize("violation", VIOLATIONS)
def test_memory_bus_protocol_rejects_violation(
    protocol_checker_build: tuple,
    violation: str,
) -> None:
    """Require each illegal traffic class to terminate assertion-enabled simulation."""
    runner, build_dir, build_root = protocol_checker_build
    results_path = build_root / "results" / f"cocotb-memory-bus-protocol-{violation}.xml"
    log_path = build_root / "results" / f"memory-bus-protocol-{violation}.log"
    with pytest.raises(RuntimeError, match="Command failed with return code"):
        runner.test(
            test_module="cocotb_memory_bus_protocol_violation",
            hdl_toplevel="memory_bus_protocol_top",
            build_dir=build_dir,
            test_dir=TESTBENCH_DIR,
            seed=int(os.environ.get("RANDOM_SEED", "1")),
            extra_env={"PROTOCOL_VIOLATION": violation},
            results_xml=str(results_path),
            log_file=log_path,
        )
    assert VIOLATION_MARKERS[violation] in log_path.read_text(encoding="utf-8")
