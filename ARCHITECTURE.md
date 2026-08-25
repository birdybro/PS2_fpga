# Architecture

PS2_fpga will separate synthesizable SystemVerilog under `rtl/` from
simulation-only models, loaders, and debug facilities under `sim/`. Reference
models will live under `reference/`, and verification will be divided into
unit, differential, randomized, integration, regression, and system tests.

The first implementation target is a deliberately simple multi-cycle R5900
execution core connected to behavioral memory. Pipeline and timing accuracy
are later, explicitly tracked work.

## Repository boundaries

- `rtl/` contains synthesis-oriented hardware organized by PS2 subsystem.
- `sim/` contains non-synthesizable models, loaders, debug, and the simulation top.
- `reference/` contains correctness-oriented models independent from the RTL.
- `tests/` separates unit, differential, randomized, integration, regression,
  and system verification.
- `software/` contains source for legal, purpose-built bare-metal workloads.
- `scripts/` contains reproducible development and validation entry points.
- `docs/` contains detailed subsystem documentation as it is developed.
- `.github/workflows/` contains continuous-integration definitions.

## Accuracy status

- Functional accuracy: not yet implemented.
- Architectural accuracy: not yet implemented.
- Timing accuracy: not yet implemented.
- FPGA readiness: not yet assessed.
