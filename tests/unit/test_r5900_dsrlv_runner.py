"""Pytest orchestration for directed R5900 DSRLV tests."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

ROOT = Path(__file__).resolve().parents[2]
TEST_DIR = Path(__file__).resolve().parent / "r5900_dsrlv"
HARNESS = Path(__file__).resolve().parent / "r5900_shift_immediate"
COCOTB_TEST_COUNT = 3


def sources() -> list[Path]:
    return [
        ROOT / "rtl/ee/r5900/r5900_types_pkg.sv",
        ROOT / "rtl/ee/r5900/r5900_pc.sv",
        ROOT / "rtl/ee/r5900/r5900_gpr_storage.sv",
        ROOT / "rtl/ee/r5900/r5900_gpr_file.sv",
        ROOT / "rtl/ee/r5900/r5900_decode.sv",
        ROOT / "rtl/ee/r5900/r5900_decode_dispatch.sv",
        ROOT / "rtl/ee/r5900/r5900_writeback.sv",
        ROOT / "rtl/ee/r5900/r5900_execute.sv",
        HARNESS / "r5900_shift_immediate_top.sv",
    ]


@pytest.mark.unit
def test_r5900_dsrlv_directed() -> None:
    build = Path(os.environ.get("PS2_BUILD_ROOT", ROOT / "build"))
    runner = get_runner("verilator")
    directory = build / "pytest/r5900_dsrlv_directed"
    runner.build(
        sources=sources(),
        hdl_toplevel="r5900_shift_immediate_top",
        build_args=["-Wall", "--assert", "--timing"],
        build_dir=directory,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_r5900_dsrlv",
        hdl_toplevel="r5900_shift_immediate_top",
        build_dir=directory,
        test_dir=TEST_DIR,
        seed=int(os.environ.get("RANDOM_SEED", "1")),
        results_xml=str(build / "results/cocotb-r5900-dsrlv-directed.xml"),
    )
    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == COCOTB_TEST_COUNT
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
