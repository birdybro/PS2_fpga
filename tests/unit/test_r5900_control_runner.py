"""Pytest orchestration for R5900 functional control-state verification."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "r5900_control"
COCOTB_TEST_COUNT = 2


@pytest.fixture(scope="module")
def control_build() -> tuple:
    """Build one assertion-enabled control executable for legal and illegal cases."""
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "r5900_control"
    runner = get_runner("verilator")
    runner.build(
        sources=[
            REPO_ROOT / "rtl/ee/r5900/r5900_types_pkg.sv",
            REPO_ROOT / "rtl/ee/r5900/r5900_control_state_checker.sv",
            REPO_ROOT / "rtl/ee/r5900/r5900_control.sv",
            TESTBENCH_DIR / "r5900_control_top.sv",
        ],
        hdl_toplevel="r5900_control_top",
        build_args=["-Wall", "--assert", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    return runner, build_dir, build_root


@pytest.mark.unit
def test_r5900_control_legal_transitions(control_build: tuple) -> None:
    """Verify typed state width, stalls, legal ordering, irrelevant events, and reset."""
    runner, build_dir, build_root = control_build
    results_path = build_root / "results" / "cocotb-r5900-control-valid.xml"
    result = runner.test(
        test_module="cocotb_r5900_control_valid",
        hdl_toplevel="r5900_control_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=int(os.environ.get("RANDOM_SEED", "1")),
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == COCOTB_TEST_COUNT
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")


@pytest.mark.unit
def test_r5900_control_illegal_state_is_fatal(control_build: tuple) -> None:
    """Prove the legal-state assertion terminates required simulation."""
    runner, build_dir, build_root = control_build
    results_path = build_root / "results" / "cocotb-r5900-control-illegal.xml"
    log_path = build_root / "results" / "r5900-control-illegal.log"
    with pytest.raises(RuntimeError, match="Command failed with return code"):
        runner.test(
            test_module="cocotb_r5900_control_illegal",
            hdl_toplevel="r5900_control_top",
            build_dir=build_dir,
            test_dir=TESTBENCH_DIR,
            seed=int(os.environ.get("RANDOM_SEED", "1")),
            results_xml=str(results_path),
            log_file=log_path,
        )
    assert "R5900_CONTROL_STATE" in log_path.read_text(encoding="utf-8")
