"""Pytest orchestration for arithmetic EE ELF execution on the R5900 core."""

import os
import struct
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

from sim.loaders.elf32 import load_ee_elf32_image

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "r5900_arithmetic_elf"
RAM_SIZE = 256
SEGMENT_ADDRESS = 0x40
ENTRY_POINT = 0x44
FILE_OFFSET = 0x100
PREFIX_WORD = 0x240C_0055
EXPECTED_PROGRAM_WORDS = (
    0x3C01_1234,
    0x3421_5678,
    0x2402_FFFF,
    0x3823_FFFF,
    0x3064_00FF,
    0x0024_2821,
    0x0081_3023,
    0x00C0_382A,
    0x00C0_402B,
    0x28C9_0000,
    0x2C0A_FFFF,
    0x0024_5827,
    0x0000_0000,
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


def encode_i_type(opcode: int, rs: int, rt: int, immediate: int) -> int:
    """Encode one I-type word from independent field positions."""
    return (opcode << 26) | (rs << 21) | (rt << 16) | (immediate & 0xFFFF)


def encode_r_type(rs: int, rt: int, rd: int, function: int) -> int:
    """Encode one zero-shift SPECIAL word from independent field positions."""
    return (rs << 21) | (rt << 16) | (rd << 11) | function


def build_program_words() -> tuple[int, ...]:
    """Construct the arithmetic stream without reusing the expected literals."""
    return (
        encode_i_type(0x0F, 0, 1, 0x1234),
        encode_i_type(0x0D, 1, 1, 0x5678),
        encode_i_type(0x09, 0, 2, -1),
        encode_i_type(0x0E, 1, 3, 0xFFFF),
        encode_i_type(0x0C, 3, 4, 0x00FF),
        encode_r_type(1, 4, 5, 0x21),
        encode_r_type(4, 1, 6, 0x23),
        encode_r_type(6, 0, 7, 0x2A),
        encode_r_type(6, 0, 8, 0x2B),
        encode_i_type(0x0A, 6, 9, 0),
        encode_i_type(0x0B, 0, 10, -1),
        encode_r_type(1, 4, 11, 0x27),
        0,
    )


def build_ee_elf(program_words: tuple[int, ...]) -> tuple[bytes, bytes]:
    """Build one native little-endian executable with a skipped prefix word."""
    segment = b"".join(word.to_bytes(4, "little") for word in (PREFIX_WORD, *program_words))
    identification = bytearray(16)
    identification[:7] = b"\x7fELF\x01\x01\x01"
    header = bytes(identification) + struct.pack(
        "<HHIIIIIHHHHHH",
        2,
        8,
        1,
        ENTRY_POINT,
        52,
        0,
        0x2092_4001,
        52,
        32,
        1,
        40,
        0,
        0,
    )
    program_header = struct.pack(
        "<IIIIIIII",
        1,
        FILE_OFFSET,
        SEGMENT_ADDRESS,
        SEGMENT_ADDRESS,
        len(segment),
        len(segment),
        5,
        0x10,
    )
    image = bytearray(FILE_OFFSET + len(segment))
    image[: len(header)] = header
    image[52 : 52 + len(program_header)] = program_header
    image[FILE_OFFSET:] = segment
    return bytes(image), segment


def parse_trace_record(line: str) -> dict[str, int]:
    """Parse one stable key-value architectural trace line."""
    fields = dict(field.split("=", maxsplit=1) for field in line.split())
    return {
        key: int(value, 16 if key == "sequence" or value.startswith("0x") else 10)
        for key, value in fields.items()
    }


def assert_arithmetic_trace(trace_path: Path) -> None:
    """Require exact EE retirement payloads and deterministic trace cycles."""
    lines = trace_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# PS2_fpga architectural event trace v1"
    records = tuple(parse_trace_record(line) for line in lines[1:])
    assert len(records) == len(EXPECTED_PROGRAM_WORDS)
    for index, (record, instruction) in enumerate(
        zip(records, EXPECTED_PROGRAM_WORDS, strict=True)
    ):
        assert record == {
            "cycle": 64 + (8 * index),
            "sequence": index,
            "source": 0x01,
            "kind": 0x01,
            "pc": ENTRY_POINT + (4 * index),
            "instruction": instruction,
            "identifier": 0,
            "value": 0,
        }


@pytest.mark.integration
def test_r5900_executes_arithmetic_ee_elf_with_verilator() -> None:
    """Load a generated EE ELF and require exact arithmetic state and trace."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    build_dir = build_root / "pytest" / "r5900_arithmetic_elf"
    results_path = build_root / "results" / "cocotb-r5900-arithmetic-elf.xml"
    elf_path = build_root / "inputs" / "ee-arithmetic-integration.elf"
    trace_path = build_root / "traces" / "ee-arithmetic-retirement.log"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    elf_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.unlink(missing_ok=True)

    program_words = build_program_words()
    assert program_words == EXPECTED_PROGRAM_WORDS
    elf_image, segment = build_ee_elf(program_words)
    elf_path.write_bytes(elf_image)
    memory_image = bytearray([0xA5] * RAM_SIZE)
    load_result = load_ee_elf32_image(memory_image, elf_image)
    assert load_result.entry_point == ENTRY_POINT
    assert len(load_result.segments) == 1
    assert load_result.segments[0].start_address == SEGMENT_ADDRESS
    assert load_result.segments[0].memory_end_address == SEGMENT_ADDRESS + len(segment)

    runner = get_runner("verilator")
    runner.build(
        sources=SOURCES,
        hdl_toplevel="ps2_sim_top",
        parameters={
            "RESET_CYCLES": 2,
            "RAM_SIZE_BYTES": RAM_SIZE,
            "RAM_RESPONSE_LATENCY_CYCLES": 1,
            "MAX_CYCLES": 192,
            "FINISH_ON_PASS": 0,
            "ARCH_TRACE_ENABLE": 1,
            "R5900_CORE_ENABLE": 1,
        },
        build_args=["-Wall", "--assert", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_r5900_arithmetic_elf",
        hdl_toplevel="ps2_sim_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        extra_env={
            "SIM_ENTRY_POINT": str(load_result.entry_point),
            "SIM_MEMORY_IMAGE_HEX": memory_image.hex(),
            "SIM_PROGRAM_END": str(ENTRY_POINT + (4 * len(program_words))),
            "SIM_SEGMENT_END": str(load_result.segments[0].memory_end_address),
            "SIM_SEGMENT_START": str(load_result.segments[0].start_address),
        },
        plusargs=[f"+ARCH_TRACE_FILE={trace_path}"],
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
    assert_arithmetic_trace(trace_path)
