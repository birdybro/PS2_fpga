"""Pytest orchestration for differential 128-bit behavioral RAM reads."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "behavioral_system_ram"
UNIT_TOP_DIR = REPO_ROOT / "tests/unit/behavioral_system_ram"


@pytest.mark.differential
def test_behavioral_system_ram_read128_against_python_model() -> None:
    """Compare all aligned quadwords with an independent byte model."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "behavioral_system_ram_read128_differential"
    results_path = build_root / "results" / "cocotb-ram-read128-differential.xml"
    results_path.parent.mkdir(parents=True, exist_ok=True)

    runner = get_runner("verilator")
    runner.build(
        sources=[
            REPO_ROOT / "rtl/memory/memory_bus_if.sv",
            REPO_ROOT / "sim/models/behavioral_system_ram.sv",
            UNIT_TOP_DIR / "behavioral_system_ram_bus_top.sv",
        ],
        hdl_toplevel="behavioral_system_ram_bus_top",
        parameters={"SIZE_BYTES": 256},
        build_args=["-Wall", "--assert", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_behavioral_system_ram_read128_differential",
        hdl_toplevel="behavioral_system_ram_bus_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
