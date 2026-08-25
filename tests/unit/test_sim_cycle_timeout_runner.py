"""Pytest orchestration for the simulation cycle watchdog."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "sim_cycle_timeout"
FATAL_TIMEOUT_CYCLES = 3


@pytest.mark.unit
@pytest.mark.parametrize("max_cycles", (0, 1, 4))
def test_sim_cycle_timeout_boundary_with_verilator(max_cycles: int) -> None:
    """Observe disabled, first-cycle, and multi-cycle boundaries without fatal exit."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / f"sim_cycle_timeout_{max_cycles}"
    results_path = build_root / "results" / f"cocotb-sim-cycle-timeout-{max_cycles}.xml"
    results_path.parent.mkdir(parents=True, exist_ok=True)

    runner = get_runner("verilator")
    runner.build(
        sources=[REPO_ROOT / "sim/models/sim_cycle_timeout.sv"],
        hdl_toplevel="sim_cycle_timeout",
        parameters={"MAX_CYCLES": max_cycles, "FATAL_ON_TIMEOUT": 0},
        build_args=["-Wall", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_sim_cycle_timeout",
        hdl_toplevel="sim_cycle_timeout",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        extra_env={"SIM_TIMEOUT_CYCLES": str(max_cycles)},
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")


@pytest.mark.unit
def test_sim_cycle_timeout_fatal_path_with_verilator() -> None:
    """Require the default enabled watchdog to terminate with a stable diagnostic."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "sim_cycle_timeout_fatal"
    results_path = build_root / "results" / "cocotb-sim-cycle-timeout-fatal.xml"
    log_path = build_root / "results" / "sim-cycle-timeout-fatal.log"
    results_path.parent.mkdir(parents=True, exist_ok=True)

    runner = get_runner("verilator")
    runner.build(
        sources=[REPO_ROOT / "sim/models/sim_cycle_timeout.sv"],
        hdl_toplevel="sim_cycle_timeout",
        parameters={"MAX_CYCLES": FATAL_TIMEOUT_CYCLES},
        build_args=["-Wall", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    with pytest.raises(RuntimeError, match="Command failed with return code"):
        runner.test(
            test_module="cocotb_sim_cycle_timeout_fatal",
            hdl_toplevel="sim_cycle_timeout",
            build_dir=build_dir,
            test_dir=TESTBENCH_DIR,
            seed=seed,
            extra_env={"SIM_TIMEOUT_CYCLES": str(FATAL_TIMEOUT_CYCLES)},
            results_xml=str(results_path),
            log_file=log_path,
        )
    log = log_path.read_text(encoding="utf-8")
    assert "SIM_TIMEOUT" in log
    assert f"reached {FATAL_TIMEOUT_CYCLES} active cycles" in log
