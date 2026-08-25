"""Pytest orchestration for the simulation reset cocotb testbench."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "sim_reset"


@pytest.mark.unit
def test_sim_reset_with_verilator() -> None:
    """Build clock/reset models, run cocotb, and reject failures or skips."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "sim_reset"
    results_path = build_root / "results" / "cocotb-sim-reset.xml"
    results_path.parent.mkdir(parents=True, exist_ok=True)

    runner = get_runner("verilator")
    runner.build(
        sources=[
            REPO_ROOT / "sim/models/sim_clock.sv",
            REPO_ROOT / "sim/models/sim_reset.sv",
            TESTBENCH_DIR / "sim_reset_top.sv",
        ],
        hdl_toplevel="sim_reset_top",
        build_args=["-Wall", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_sim_reset",
        hdl_toplevel="sim_reset_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
