"""Pytest orchestration for the two-register integration test."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "register_pipeline"


@pytest.mark.integration
def test_two_register_pipeline_with_verilator() -> None:
    """Verify hierarchy build, simulation, XML results, and seed propagation."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "register_pipeline"
    results_path = build_root / "results" / "cocotb-register-pipeline.xml"
    results_path.parent.mkdir(parents=True, exist_ok=True)

    runner = get_runner("verilator")
    runner.build(
        sources=[
            REPO_ROOT / "rtl/common/register_en.sv",
            TESTBENCH_DIR / "register_pipeline_top.sv",
        ],
        hdl_toplevel="register_pipeline_top",
        build_args=["-Wall"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_register_pipeline",
        hdl_toplevel="register_pipeline_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    cases = root.findall(".//testcase")
    assert len(cases) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
    properties = {
        item.attrib["name"]: item.attrib["value"]
        for item in cases[0].findall("./properties/property")
    }
    assert int(properties["random_seed"]) == seed
