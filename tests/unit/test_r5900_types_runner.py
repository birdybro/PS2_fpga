"""Pytest orchestration for R5900 type and debug-interface compilation checks."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "r5900_types"
COCOTB_TEST_COUNT = 2


@pytest.mark.unit
def test_r5900_types_and_debug_interface() -> None:
    """Compile typed state contracts and verify their flattened observation boundary."""
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "r5900_types"
    results_path = build_root / "results" / "cocotb-r5900-types.xml"
    runner = get_runner("verilator")
    runner.build(
        sources=[
            REPO_ROOT / "rtl/ee/r5900/r5900_types_pkg.sv",
            REPO_ROOT / "rtl/ee/r5900/r5900_debug_if.sv",
            TESTBENCH_DIR / "r5900_debug_driver.sv",
            TESTBENCH_DIR / "r5900_debug_probe.sv",
            TESTBENCH_DIR / "r5900_types_top.sv",
        ],
        hdl_toplevel="r5900_types_top",
        build_args=["-Wall", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_r5900_types",
        hdl_toplevel="r5900_types_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=int(os.environ.get("RANDOM_SEED", "1")),
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == COCOTB_TEST_COUNT
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
