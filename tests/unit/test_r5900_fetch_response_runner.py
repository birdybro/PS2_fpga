"""Pytest orchestration for R5900 instruction-fetch response verification."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "r5900_fetch_response"
COCOTB_TEST_COUNT = 3
VIOLATION_MARKERS = {
    "unexpected": "R5900_FETCH_RESPONSE_UNEXPECTED",
    "overlap": "R5900_FETCH_RESPONSE_OVERLAP",
}


@pytest.fixture(scope="module")
def fetch_response_build() -> tuple:
    """Build one assertion-enabled response receiver for all test cases."""
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "r5900_fetch_response"
    runner = get_runner("verilator")
    runner.build(
        sources=[
            REPO_ROOT / "rtl/ee/r5900/r5900_types_pkg.sv",
            REPO_ROOT / "rtl/memory/memory_bus_if.sv",
            REPO_ROOT / "rtl/ee/r5900/r5900_fetch_response.sv",
            TESTBENCH_DIR / "r5900_fetch_response_top.sv",
        ],
        hdl_toplevel="r5900_fetch_response_top",
        build_args=["-Wall", "--assert", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    return runner, build_dir, build_root


@pytest.mark.unit
def test_r5900_fetch_response_legal_traffic(fetch_response_build: tuple) -> None:
    """Verify capture, backpressure, error state, same-cycle response, and reset."""
    runner, build_dir, build_root = fetch_response_build
    results_path = build_root / "results" / "cocotb-r5900-fetch-response-valid.xml"
    result = runner.test(
        test_module="cocotb_r5900_fetch_response_valid",
        hdl_toplevel="r5900_fetch_response_top",
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
@pytest.mark.parametrize("violation", tuple(VIOLATION_MARKERS))
def test_r5900_fetch_response_rejects_invalid_traffic(
    fetch_response_build: tuple,
    violation: str,
) -> None:
    """Require unsolicited responses and overlapping requests to be fatal."""
    runner, build_dir, build_root = fetch_response_build
    results_path = build_root / "results" / f"cocotb-r5900-fetch-response-{violation}.xml"
    log_path = build_root / "results" / f"r5900-fetch-response-{violation}.log"
    with pytest.raises(RuntimeError, match="Command failed with return code"):
        runner.test(
            test_module="cocotb_r5900_fetch_response_invalid",
            hdl_toplevel="r5900_fetch_response_top",
            build_dir=build_dir,
            test_dir=TESTBENCH_DIR,
            seed=int(os.environ.get("RANDOM_SEED", "1")),
            extra_env={"FETCH_RESPONSE_VIOLATION": violation},
            results_xml=str(results_path),
            log_file=log_path,
        )
    assert VIOLATION_MARKERS[violation] in log_path.read_text(encoding="utf-8")
