"""Pytest orchestration for randomized R5900 instruction-field verification."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "r5900_instruction_fields"


@pytest.mark.randomized
def test_r5900_instruction_fields_randomized() -> None:
    """Compare deterministic random words against an independent Python extraction."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "r5900_instruction_fields_randomized"
    results_path = build_root / "results" / "cocotb-r5900-instruction-fields-randomized.xml"
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
        test_module="cocotb_r5900_instruction_fields_randomized",
        hdl_toplevel="r5900_instruction_fields",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
