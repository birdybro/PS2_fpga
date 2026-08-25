"""Pytest orchestration for raw-file loading through the composed platform."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

from sim.loaders.raw_binary import load_raw_binary_file

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "ps2_sim_raw_loader"
RAM_SIZE = 128
LOAD_ADDRESS = 32
SENTINEL = 0xA5
RAW_PAYLOAD = bytes.fromhex(
    "00 01 7f 80 fe ff 55 aa 10 20 30 40 50 60 70 80 "
    "ff 00 ff 00 aa 55 aa 55 de ad be ef 12 34 56 78"
)
SOURCES = [
    REPO_ROOT / "rtl/memory/memory_bus_if.sv",
    REPO_ROOT / "rtl/memory/memory_bus_protocol_checker.sv",
    REPO_ROOT / "sim/models/behavioral_system_ram.sv",
    REPO_ROOT / "sim/models/sim_clock.sv",
    REPO_ROOT / "sim/models/sim_reset.sv",
    REPO_ROOT / "sim/models/sim_cycle_timeout.sv",
    REPO_ROOT / "sim/models/sim_termination.sv",
    REPO_ROOT / "sim/debug/memory_transaction_trace.sv",
    REPO_ROOT / "sim/debug/architectural_trace_sink.sv",
    REPO_ROOT / "sim/debug/sim_waveform_control.sv",
    REPO_ROOT / "sim/ps2_sim_top.sv",
]


@pytest.mark.integration
def test_raw_binary_loader_through_platform_ram_with_verilator() -> None:
    """Load an external raw file and require exact transaction readback."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "ps2_sim_raw_loader"
    results_path = build_root / "results" / "cocotb-ps2-sim-raw-loader.xml"
    raw_path = build_root / "inputs" / "raw-platform-integration.bin"
    build_dir.mkdir(parents=True, exist_ok=True)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(RAW_PAYLOAD)

    memory_image = bytearray([SENTINEL] * RAM_SIZE)
    load_result = load_raw_binary_file(memory_image, raw_path, LOAD_ADDRESS)
    assert load_result.start_address == LOAD_ADDRESS
    assert load_result.size_bytes == len(RAW_PAYLOAD)
    assert load_result.end_address == LOAD_ADDRESS + len(RAW_PAYLOAD)

    runner = get_runner("verilator")
    runner.build(
        sources=SOURCES,
        hdl_toplevel="ps2_sim_top",
        parameters={"RESET_CYCLES": 2, "RAM_SIZE_BYTES": RAM_SIZE},
        build_args=["-Wall", "--assert", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_ps2_sim_raw_loader",
        hdl_toplevel="ps2_sim_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        extra_env={
            "SIM_LOAD_ADDRESS": str(LOAD_ADDRESS),
            "SIM_RAM_IMAGE_HEX": memory_image.hex(),
            "SIM_RAM_SIZE": str(RAM_SIZE),
            "SIM_RAW_BINARY_PATH": str(raw_path),
            "SIM_SENTINEL": str(SENTINEL),
        },
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
