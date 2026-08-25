"""Pytest orchestration for centralized R5900 architectural writeback tests."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "r5900_writeback"
COCOTB_TEST_COUNT = 4


@pytest.mark.unit
def test_r5900_writeback_directed() -> None:
    """Verify destinations, 128-bit values, zero suppression, one-shot behavior, and reset."""
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "r5900_writeback_directed"
    results_path = build_root / "results" / "cocotb-r5900-writeback-directed.xml"
    runner = get_runner("verilator")
    runner.build(
        sources=[
            REPO_ROOT / "rtl/ee/r5900/r5900_types_pkg.sv",
            REPO_ROOT / "rtl/ee/r5900/r5900_gpr_storage.sv",
            REPO_ROOT / "rtl/ee/r5900/r5900_gpr_file.sv",
            REPO_ROOT / "rtl/ee/r5900/r5900_writeback.sv",
            TESTBENCH_DIR / "r5900_writeback_top.sv",
        ],
        hdl_toplevel="r5900_writeback_top",
        build_args=["-Wall", "--assert", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_r5900_writeback",
        hdl_toplevel="r5900_writeback_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=int(os.environ.get("RANDOM_SEED", "1")),
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == COCOTB_TEST_COUNT
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
