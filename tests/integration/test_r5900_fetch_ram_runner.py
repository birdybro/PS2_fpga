"""Pytest orchestration for the R5900 fetch-to-RAM integration path."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "r5900_fetch_ram"
SOURCES = [
    REPO_ROOT / "rtl/ee/r5900/r5900_types_pkg.sv",
    REPO_ROOT / "rtl/memory/memory_bus_if.sv",
    REPO_ROOT / "rtl/memory/memory_bus_protocol_checker.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_fetch_request.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_fetch_response.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_fetch_path.sv",
    REPO_ROOT / "sim/models/behavioral_system_ram.sv",
    REPO_ROOT / "sim/models/sim_clock.sv",
    REPO_ROOT / "sim/models/sim_reset.sv",
    REPO_ROOT / "sim/models/sim_cycle_timeout.sv",
    REPO_ROOT / "sim/models/sim_termination.sv",
    REPO_ROOT / "sim/debug/memory_transaction_trace.sv",
    REPO_ROOT / "sim/debug/architectural_trace_sink.sv",
    REPO_ROOT / "sim/debug/sim_waveform_control.sv",
    REPO_ROOT / "sim/ps2_sim_top.sv",
]


@pytest.mark.integration
def test_r5900_fetch_path_reads_platform_ram_with_verilator() -> None:
    """Fetch two words with fixed RAM latency and instruction backpressure."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "r5900_fetch_ram"
    results_path = build_root / "results" / "cocotb-r5900-fetch-ram.xml"
    results_path.parent.mkdir(parents=True, exist_ok=True)

    runner = get_runner("verilator")
    runner.build(
        sources=SOURCES,
        hdl_toplevel="ps2_sim_top",
        parameters={
            "RESET_CYCLES": 2,
            "RAM_SIZE_BYTES": 128,
            "RAM_RESPONSE_LATENCY_CYCLES": 2,
            "R5900_FETCH_ENABLE": 1,
        },
        build_args=["-Wall", "--assert", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_r5900_fetch_ram",
        hdl_toplevel="ps2_sim_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
