"""Pytest orchestration for EE ELF loading through the composed platform."""

import os
from collections.abc import Sequence
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

from sim.loaders.elf32 import load_ee_elf32_image

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "ps2_sim_elf_loader"
RAM_SIZE = 256
SENTINEL = 0xA5
ENTRY_POINT = 0x44
FIRST_PAYLOAD = bytes.fromhex("10 32 54 76 98 ba dc fe 01 23 45 67 89 ab cd ef")
SECOND_PAYLOAD = bytes.fromhex("ff ee dd cc bb aa 99 88")
PROGRAM_HEADERS = (
    (1, 0x100, 0x40, 0xDEAD_0040, len(FIRST_PAYLOAD), 0x20, 5, 0x10),
    (1, 0x120, 0xA0, 0xDEAD_00A0, len(SECOND_PAYLOAD), 0x10, 6, 0x10),
)
HEADER_FIELD_LAYOUT = (
    (2, 2),
    (8, 2),
    (1, 4),
    (ENTRY_POINT, 4),
    (52, 4),
    (0, 4),
    (0x2092_4001, 4),
    (52, 2),
    (32, 2),
    (len(PROGRAM_HEADERS), 2),
    (40, 2),
    (0, 2),
    (0, 2),
)
SOURCES = [
    REPO_ROOT / "rtl/ee/r5900/r5900_types_pkg.sv",
    REPO_ROOT / "rtl/memory/memory_bus_if.sv",
    REPO_ROOT / "rtl/memory/memory_bus_protocol_checker.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_control_state_checker.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_control.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_pc.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_fetch_request.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_fetch_response.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_fetch_path.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_decode.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_decode_dispatch.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_execute.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_writeback.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_gpr_storage.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_gpr_file.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_hilo_state.sv",
    REPO_ROOT / "rtl/ee/r5900/r5900_core.sv",
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


def encode_fields(fields: Sequence[tuple[int, int]]) -> bytes:
    """Encode little-endian fixture fields without using production parser layouts."""
    return b"".join(value.to_bytes(width, "little") for value, width in fields)


def build_ee_elf_fixture() -> bytes:
    """Build a two-segment little-endian EE executable independently."""
    identification = bytearray(16)
    identification[:7] = b"\x7fELF\x01\x01\x01"
    header = bytes(identification) + encode_fields(HEADER_FIELD_LAYOUT)
    program_header_table = b"".join(
        encode_fields(tuple((value, 4) for value in program_header))
        for program_header in PROGRAM_HEADERS
    )
    image = bytearray(0x120 + len(SECOND_PAYLOAD))
    image[:52] = header
    image[52 : 52 + len(program_header_table)] = program_header_table
    image[0x100 : 0x100 + len(FIRST_PAYLOAD)] = FIRST_PAYLOAD
    image[0x120 : 0x120 + len(SECOND_PAYLOAD)] = SECOND_PAYLOAD
    return bytes(image)


@pytest.mark.integration
def test_ee_elf_loader_through_platform_ram_with_verilator() -> None:
    """Load EE segments and require exact file, BSS, gap, and entry readback."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "ps2_sim_elf_loader"
    results_path = build_root / "results" / "cocotb-ps2-sim-elf-loader.xml"
    elf_path = build_root / "inputs" / "ee-platform-integration.elf"
    build_dir.mkdir(parents=True, exist_ok=True)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    elf_path.parent.mkdir(parents=True, exist_ok=True)
    elf_path.write_bytes(build_ee_elf_fixture())

    memory_image = bytearray([SENTINEL] * RAM_SIZE)
    load_result = load_ee_elf32_image(memory_image, elf_path.read_bytes())
    assert load_result.entry_point == ENTRY_POINT
    assert tuple(
        (
            segment.program_header_index,
            segment.file_offset,
            segment.start_address,
            segment.file_size_bytes,
            segment.memory_size_bytes,
        )
        for segment in load_result.segments
    ) == (
        (0, 0x100, 0x40, len(FIRST_PAYLOAD), 0x20),
        (1, 0x120, 0xA0, len(SECOND_PAYLOAD), 0x10),
    )
    segment_ranges = ",".join(
        f"{segment.start_address}:{segment.memory_end_address}" for segment in load_result.segments
    )

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
        test_module="cocotb_ps2_sim_elf_loader",
        hdl_toplevel="ps2_sim_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        extra_env={
            "SIM_ELF_PATH": str(elf_path),
            "SIM_ENTRY_POINT": str(load_result.entry_point),
            "SIM_RAM_IMAGE_HEX": memory_image.hex(),
            "SIM_RAM_SIZE": str(RAM_SIZE),
            "SIM_SEGMENT_RANGES": segment_ranges,
            "SIM_SENTINEL": str(SENTINEL),
        },
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
