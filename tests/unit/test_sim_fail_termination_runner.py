"""Pytest orchestration for simulation FAIL termination."""

import os
import subprocess
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "sim_termination"
TERMINATION_SOURCE = REPO_ROOT / "sim/models/sim_termination.sv"
EXPECTED_FAIL_CODE_TEXT = "deadbeef"


@pytest.mark.unit
def test_sim_fail_code_and_priority_state_with_verilator() -> None:
    """Observe code capture, one-shot behavior, reset, and FAIL-over-PASS priority."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "sim_fail_termination"
    results_path = build_root / "results" / "cocotb-sim-fail-termination.xml"
    results_path.parent.mkdir(parents=True, exist_ok=True)

    runner = get_runner("verilator")
    runner.build(
        sources=[TERMINATION_SOURCE],
        hdl_toplevel="sim_termination",
        parameters={"FINISH_ON_PASS": 0, "FATAL_ON_FAIL": 0},
        build_args=["-Wall", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_sim_fail_termination",
        hdl_toplevel="sim_termination",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")


@pytest.mark.unit
def test_sim_fail_default_path_fatals_standalone_simulation() -> None:
    """Require simultaneous FAIL to beat PASS, print its code, and exit nonzero."""
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "sim_fail_fatal_binary"
    binary_path = build_dir / "sim_fail_fatal"
    build_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "verilator",
            "--binary",
            "-Wall",
            "--timing",
            "--Mdir",
            str(build_dir),
            "--top-module",
            "sim_fail_fatal_top",
            "-o",
            binary_path.name,
            str(TERMINATION_SOURCE),
            str(TESTBENCH_DIR / "sim_fail_fatal_top.sv"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    completed = subprocess.run(
        [str(binary_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode != 0
    assert output.count("SIM_FAIL: code=0x") == 1
    assert EXPECTED_FAIL_CODE_TEXT in output.lower()
    assert "SIM_PASS" not in output
    assert "did not terminate" not in output
    assert "standalone test timed out" not in output
