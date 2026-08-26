"""Pytest orchestration for randomized differential R5900 MULT1 verification."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = REPO_ROOT / "tests/unit/r5900_mult1"
TESTBENCH_DIR = Path(__file__).resolve().parent / "r5900_mult1"


def mult1_sources() -> list[Path]:
    """Return ordered RTL and harness sources for MULT1 execution."""
    return [
        REPO_ROOT / "rtl/ee/r5900/r5900_types_pkg.sv",
        REPO_ROOT / "rtl/ee/r5900/r5900_pc.sv",
        REPO_ROOT / "rtl/ee/r5900/r5900_gpr_storage.sv",
        REPO_ROOT / "rtl/ee/r5900/r5900_gpr_file.sv",
        REPO_ROOT / "rtl/ee/r5900/r5900_hilo_state.sv",
        REPO_ROOT / "rtl/ee/r5900/r5900_decode.sv",
        REPO_ROOT / "rtl/ee/r5900/r5900_decode_dispatch.sv",
        REPO_ROOT / "rtl/ee/r5900/r5900_writeback.sv",
        REPO_ROOT / "rtl/ee/r5900/r5900_execute.sv",
        HARNESS_DIR / "r5900_mult1_top.sv",
    ]


@pytest.mark.differential
@pytest.mark.randomized
def test_r5900_mult1_randomized_differential() -> None:
    """Compare MULT1 state and events against the Python architectural model."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "r5900_mult1_differential"
    results_path = build_root / "results" / "cocotb-r5900-mult1-differential.xml"
    runner = get_runner("verilator")
    runner.build(
        sources=mult1_sources(),
        hdl_toplevel="r5900_mult1_top",
        build_args=["-Wall", "--assert", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_r5900_mult1_differential",
        hdl_toplevel="r5900_mult1_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
