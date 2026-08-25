"""Standalone Verilator tests for opt-in simulation waveform control."""

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTBENCH_DIR = Path(__file__).resolve().parent / "sim_waveform_control"
WAVEFORM_SOURCE = REPO_ROOT / "sim/debug/sim_waveform_control.sv"


@pytest.mark.unit
@pytest.mark.parametrize("wave_enabled", (False, True))
def test_sim_waveform_control_with_verilator(wave_enabled: bool) -> None:
    """Require disabled silence or a populated enabled VCD."""
    build_root = Path(os.environ.get("PS2_BUILD_ROOT", REPO_ROOT / "build"))
    suffix = "enabled" if wave_enabled else "disabled"
    build_dir = build_root / "pytest" / f"sim_waveform_control_{suffix}"
    binary_path = build_dir / f"sim_waveform_control_{suffix}"
    retain_wave = wave_enabled and os.environ.get("PS2_WAVES") == "1"
    if retain_wave:
        wave_path = build_root / "waves" / "sim_waveform_control" / "dump.vcd"
    else:
        wave_path = build_dir / "dump.vcd"
    build_dir.mkdir(parents=True, exist_ok=True)
    wave_path.parent.mkdir(parents=True, exist_ok=True)
    wave_path.unlink(missing_ok=True)

    subprocess.run(
        [
            "verilator",
            "--binary",
            "-Wall",
            "--timing",
            "--trace",
            "--Mdir",
            str(build_dir),
            "--top-module",
            "sim_waveform_control_top",
            f"-GWAVE_ENABLE={int(wave_enabled)}",
            "-o",
            binary_path.name,
            str(WAVEFORM_SOURCE),
            str(TESTBENCH_DIR / "sim_waveform_control_top.sv"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    completed = subprocess.run(
        [str(binary_path), f"+WAVE_FILE={wave_path}"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    if wave_enabled:
        waveform = wave_path.read_text(encoding="utf-8")
        assert "$enddefinitions $end" in waveform
        assert "probe_q" in waveform
        assert "#5000" in waveform
        if not retain_wave:
            wave_path.unlink()
            assert not wave_path.exists()
    else:
        assert not wave_path.exists()
