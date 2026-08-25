"""Pytest orchestration for deterministic architectural event tracing."""

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "architectural_trace_sink"
EXPECTED_TRACE = """# PS2_fpga architectural event trace v1
cycle=00000002 sequence=0000000000000000 source=0x01 kind=0x01 pc=0x00100000 instruction=0x00000000 identifier=0x0000 value=0x00000000000000000000000000000000
cycle=00000003 sequence=0000000000000001 source=0x01 kind=0x02 pc=0x00100004 instruction=0x34051234 identifier=0x0005 value=0x0123456789abcdeffedcba9876543210
cycle=00000005 sequence=0000000000000002 source=0x01 kind=0x03 pc=0x80000180 instruction=0x0000000d identifier=0x000a value=0x00000000000000000000000080000180
"""


@pytest.mark.unit
@pytest.mark.parametrize("trace_enabled", (False, True))
def test_architectural_trace_sink_with_verilator(trace_enabled: bool) -> None:
    """Require disabled silence or the exact enabled event schema."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    suffix = "enabled" if trace_enabled else "disabled"
    build_dir = build_root / "pytest" / f"architectural_trace_sink_{suffix}"
    results_path = build_root / "results" / f"cocotb-architectural-trace-{suffix}.xml"
    trace_path = build_root / "traces" / f"architectural-trace-{suffix}.log"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.unlink(missing_ok=True)

    runner = get_runner("verilator")
    runner.build(
        sources=[
            REPO_ROOT / "sim/debug/architectural_trace_sink.sv",
            TESTBENCH_DIR / "architectural_trace_sink_top.sv",
        ],
        hdl_toplevel="architectural_trace_sink_top",
        parameters={"TRACE_ENABLE": int(trace_enabled)},
        build_args=["-Wall", "--timing"],
        build_dir=build_dir,
        always=True,
    )
    result = runner.test(
        test_module="cocotb_architectural_trace_sink",
        hdl_toplevel="architectural_trace_sink_top",
        build_dir=build_dir,
        test_dir=TESTBENCH_DIR,
        seed=seed,
        plusargs=[f"+ARCH_TRACE_FILE={trace_path}"],
        results_xml=str(results_path),
    )

    root = ElementTree.parse(result).getroot()
    assert len(root.findall(".//testcase")) == 1
    assert not root.findall(".//failure")
    assert not root.findall(".//skipped")
    if trace_enabled:
        assert trace_path.read_text(encoding="utf-8") == EXPECTED_TRACE
    else:
        assert not trace_path.exists()
