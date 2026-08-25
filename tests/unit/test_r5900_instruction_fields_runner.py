"""Pytest orchestration for directed R5900 instruction-field tests."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "r5900_instruction_fields"
COCOTB_TEST_COUNT = 3


@pytest.mark.unit
def test_r5900_instruction_fields_directed() -> None:
    """Build the pure field extractor and verify every MIPS-format view."""
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "r5900_instruction_fields_directed"
    results_path = build_root / "results" / "cocotb-r5900-instruction-fields-directed.xml"
    runner = get_runner("verilator")
    runner.build(
        sources=[
            REPO_ROOT / "rtl/ee/r5900/r5900_types_pkg.sv",
            REPO_ROOT / "rtl/ee/r5900/r5900_instruction_fields.sv",
        ],
        hdl_toplevel="r5900_instruction_fields",
        build_args=["-Wall", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_r5900_instruction_fields",
        hdl_toplevel="r5900_instruction_fields",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=int(os.environ.get("RANDOM_SEED", "1")),
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == COCOTB_TEST_COUNT
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
