"""Pytest orchestration for the memory transaction interface smoke test."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "memory_bus_if"


@pytest.mark.unit
def test_memory_bus_interface_with_verilator() -> None:
    """Elaborate both modports and verify their complete signal connectivity."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "memory_bus_if"
    results_path = build_root / "results" / "cocotb-memory-bus-if.xml"
    results_path.parent.mkdir(parents=True, exist_ok=True)

    runner = get_runner("verilator")
    runner.build(
        sources=[
            REPO_ROOT / "rtl/memory/memory_bus_if.sv",
            TESTBENCH_DIR / "memory_bus_initiator_bridge.sv",
            TESTBENCH_DIR / "memory_bus_target_bridge.sv",
            TESTBENCH_DIR / "memory_bus_if_smoke_top.sv",
        ],
        hdl_toplevel="memory_bus_if_smoke_top",
        build_args=["-Wall", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_memory_bus_if",
        hdl_toplevel="memory_bus_if_smoke_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
