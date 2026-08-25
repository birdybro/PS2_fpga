"""Pytest orchestration for behavioral byte-addressed system RAM."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "behavioral_system_ram"


@pytest.mark.unit
def test_behavioral_system_ram_with_verilator() -> None:
    """Verify byte boundaries, out-of-range rejection, and reset retention."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "behavioral_system_ram"
    results_path = build_root / "results" / "cocotb-behavioral-system-ram.xml"
    results_path.parent.mkdir(parents=True, exist_ok=True)

    runner = get_runner("verilator")
    runner.build(
        sources=[REPO_ROOT / "sim/models/behavioral_system_ram.sv"],
        hdl_toplevel="behavioral_system_ram",
        parameters={"SIZE_BYTES": 256},
        build_args=["-Wall", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_behavioral_system_ram",
        hdl_toplevel="behavioral_system_ram",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
