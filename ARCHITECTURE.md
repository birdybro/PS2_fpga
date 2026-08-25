# Architecture

PS2_fpga will separate synthesizable SystemVerilog under `rtl/` from
simulation-only models, loaders, and debug facilities under `sim/`. Reference
models will live under `reference/`, and verification will be divided into
unit, differential, randomized, integration, regression, and system tests.

The first implementation target is a deliberately simple multi-cycle R5900
execution core connected to behavioral memory. Pipeline and timing accuracy
are later, explicitly tracked work. `docs/R5900_FOUNDATION.md` defines the
initial state, control, evidence, verification, and deferral boundaries.

## Repository boundaries

- `rtl/` contains synthesis-oriented hardware organized by PS2 subsystem.
- `sim/` contains non-synthesizable models, loaders, debug, and the simulation top.
- `reference/` contains correctness-oriented models independent from the RTL.
- `coverage/` contains machine-readable architectural feature and verification state.
- `tests/` separates unit, differential, randomized, integration, regression,
  and system verification.
- `software/` contains source for legal, purpose-built bare-metal workloads.
- `scripts/` contains reproducible development and validation entry points.
- `docs/` contains detailed subsystem documentation as it is developed.
- `.github/workflows/` contains continuous-integration definitions.

## Simulation composition boundary

`sim/ps2_sim_top.sv` is the first composed simulation platform. It owns the
simulation clock and reset, behavioral RAM, the single-outstanding memory
protocol checker, timeout and PASS/FAIL controls, memory and architectural trace
sinks, and waveform control. Its temporary external memory-master and
architectural-event ports let loaders and verification drive the platform
before an EE core exists. Those ports are simulation harness boundaries, not
PS2 architectural pins; later CPU integration will connect the same internal
memory transaction interface without changing the RAM contract.

The RAM byte backdoor is likewise exposed only for loaders and verification.
It cannot appear on the eventual synthesizable `rtl/ps2_top.sv` boundary.

## Accuracy status

- Functional accuracy: not yet implemented.
- Architectural accuracy: not yet implemented.
- Timing accuracy: not yet implemented.
- FPGA readiness: not yet assessed.
