"""Pytest orchestration for directed R5900 MFHI tests."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = REPO_ROOT / "tests/unit/r5900_mult"
TESTBENCH_DIR = Path(__file__).resolve().parent / "r5900_mfhi"
COCOTB_TEST_COUNT = 4


def mfhi_sources() -> list[Path]:
    """Return ordered RTL and harness sources for MFHI execution."""
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
        HARNESS_DIR / "r5900_mult_top.sv",
    ]


@pytest.mark.unit
def test_r5900_mfhi_directed() -> None:
    """Run full-width transfer, zero, PC, preservation, and legality coverage."""
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "r5900_mfhi_directed"
    runner = get_runner("verilator")
    runner.build(
        sources=mfhi_sources(),
        hdl_toplevel="r5900_mult_top",
        build_args=["-Wall", "--assert", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_r5900_mfhi",
        hdl_toplevel="r5900_mult_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        results_xml=str(build_root / "results/cocotb-r5900-mfhi-directed.xml"),
    )
    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == COCOTB_TEST_COUNT
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
