"""Pytest orchestration for the register cocotb testbench."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner


REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "register_en"


@pytest.mark.unit
def test_register_en_with_verilator() -> None:
    """Build the DUT, run cocotb, and reject failures or skipped tests."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "register_en"
    results_path = build_root / "results" / "cocotb-register-en.xml"
    results_path.parent.mkdir(parents=True, exist_ok=True)

    runner = get_runner("verilator")
    runner.build(
        sources=[REPO_ROOT / "rtl/common/register_en.sv"],
        hdl_toplevel="register_en",
        build_args=["-Wall"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_register_en",
        hdl_toplevel="register_en",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
