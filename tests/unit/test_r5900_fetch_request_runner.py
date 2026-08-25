"""Pytest orchestration for R5900 instruction-fetch request verification."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "r5900_fetch_request"
COCOTB_TEST_COUNT = 3
VIOLATION_MARKERS = {
    "alignment": "R5900_FETCH_ALIGN",
    "stalled_restart": "R5900_FETCH_RESTART",
}


@pytest.fixture(scope="module")
def fetch_request_build() -> tuple:
    """Build one assertion-enabled request issuer for all legal and illegal cases."""
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "r5900_fetch_request"
    runner = get_runner("verilator")
    runner.build(
        sources=[
            REPO_ROOT / "rtl/ee/r5900/r5900_types_pkg.sv",
            REPO_ROOT / "rtl/memory/memory_bus_if.sv",
            REPO_ROOT / "rtl/ee/r5900/r5900_fetch_request.sv",
            TESTBENCH_DIR / "r5900_fetch_request_top.sv",
        ],
        hdl_toplevel="r5900_fetch_request_top",
        build_args=["-Wall", "--assert", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    return runner, build_dir, build_root


@pytest.mark.unit
def test_r5900_fetch_request_legal_traffic(fetch_request_build: tuple) -> None:
    """Verify fields, boundary addresses, stalls, one handshake, and reset cancellation."""
    runner, build_dir, build_root = fetch_request_build
    results_path = build_root / "results" / "cocotb-r5900-fetch-request-valid.xml"
    result = runner.test(
        test_module="cocotb_r5900_fetch_request_valid",
        hdl_toplevel="r5900_fetch_request_top",
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
def test_r5900_fetch_request_rejects_invalid_start(
    fetch_request_build: tuple,
    violation: str,
) -> None:
    """Require unaligned starts and replacement of a stalled request to be fatal."""
    runner, build_dir, build_root = fetch_request_build
    results_path = build_root / "results" / f"cocotb-r5900-fetch-request-{violation}.xml"
    log_path = build_root / "results" / f"r5900-fetch-request-{violation}.log"
    with pytest.raises(RuntimeError, match="Command failed with return code"):
        runner.test(
            test_module="cocotb_r5900_fetch_request_invalid",
            hdl_toplevel="r5900_fetch_request_top",
            build_dir=build_dir,
            test_dir=TESTBENCH_DIR,
            seed=int(os.environ.get("RANDOM_SEED", "1")),
            extra_env={"FETCH_REQUEST_VIOLATION": violation},
            results_xml=str(results_path),
            log_file=log_path,
        )
    assert VIOLATION_MARKERS[violation] in log_path.read_text(encoding="utf-8")
