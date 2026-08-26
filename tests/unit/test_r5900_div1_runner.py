"""Pytest orchestration for directed R5900 DIV1 tests."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = REPO_ROOT / "tests/unit/r5900_div1"
TESTBENCH_DIR = Path(__file__).resolve().parent / "r5900_div1"
COCOTB_TEST_COUNT = 4


def div1_sources() -> list[Path]:
    """Return ordered RTL and harness sources for DIV1 execution."""
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
        HARNESS_DIR / "r5900_div1_top.sv",
    ]


@pytest.mark.unit
def test_r5900_div1_directed() -> None:
    """Run signed quotient, edge-result, and reserved-field coverage."""
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "r5900_div1_directed"
    runner = get_runner("verilator")
    runner.build(
        sources=div1_sources(),
        hdl_toplevel="r5900_div1_top",
        build_args=["-Wall", "--assert", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_r5900_div1",
        hdl_toplevel="r5900_div1_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        results_xml=str(build_root / "results/cocotb-r5900-div1-directed.xml"),
    )
    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == COCOTB_TEST_COUNT
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
