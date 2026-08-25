"""Pytest orchestration for the composed simulation platform top."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "ps2_sim_top"
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


@pytest.mark.unit
@pytest.mark.parametrize("reset_cycles", (1, 4))
def test_ps2_sim_top_reset_integration_with_verilator(reset_cycles: int) -> None:
    """Elaborate all platform blocks and verify exact reset fanout."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / f"ps2_sim_top_reset_{reset_cycles}"
    results_path = build_root / "results" / f"cocotb-ps2-sim-top-{reset_cycles}.xml"
    memory_trace = build_root / "traces" / f"platform-memory-disabled-{reset_cycles}.log"
    arch_trace = build_root / "traces" / f"platform-arch-disabled-{reset_cycles}.log"
    wave_path = build_root / "waves" / f"platform-disabled-{reset_cycles}.vcd"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    memory_trace.parent.mkdir(parents=True, exist_ok=True)
    wave_path.parent.mkdir(parents=True, exist_ok=True)
    for output_path in (memory_trace, arch_trace, wave_path):
        output_path.unlink(missing_ok=True)

    runner = get_runner("verilator")
    runner.build(
        sources=SOURCES,
        hdl_toplevel="ps2_sim_top",
        parameters={"RESET_CYCLES": reset_cycles},
        build_args=["-Wall", "--assert", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_ps2_sim_top",
        hdl_toplevel="ps2_sim_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        extra_env={"SIM_RESET_CYCLES": str(reset_cycles)},
        plusargs=[
            f"+MEM_TRACE_FILE={memory_trace}",
            f"+ARCH_TRACE_FILE={arch_trace}",
            f"+WAVE_FILE={wave_path}",
        ],
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
    assert not memory_trace.exists()
    assert not arch_trace.exists()
    assert not wave_path.exists()
