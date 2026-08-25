"""Pytest orchestration for architectural R5900 GPR-zero verification."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "r5900_gpr_file"
COCOTB_TEST_COUNT = 2


@pytest.mark.unit
def test_r5900_gpr_file_enforces_register_zero() -> None:
    """Build the architectural wrapper and verify 128-bit zero on every boundary."""
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "r5900_gpr_file"
    results_path = build_root / "results" / "cocotb-r5900-gpr-file.xml"
    runner = get_runner("verilator")
    runner.build(
        sources=[
            REPO_ROOT / "rtl/ee/r5900/r5900_types_pkg.sv",
            REPO_ROOT / "rtl/ee/r5900/r5900_gpr_storage.sv",
            REPO_ROOT / "rtl/ee/r5900/r5900_gpr_file.sv",
        ],
        hdl_toplevel="r5900_gpr_file",
        build_args=["-Wall", "--assert", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_r5900_gpr_file",
        hdl_toplevel="r5900_gpr_file",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=int(os.environ.get("RANDOM_SEED", "1")),
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == COCOTB_TEST_COUNT
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
