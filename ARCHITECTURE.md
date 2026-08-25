# Architecture

PS2_fpga will separate synthesizable SystemVerilog under `rtl/` from
simulation-only models, loaders, and debug facilities under `sim/`. Reference
models will live under `reference/`, and verification will be divided into
unit, differential, randomized, integration, regression, and system tests.

The first implementation target is a deliberately simple multi-cycle R5900
execution core connected to behavioral memory. Pipeline and timing accuracy
are later, explicitly tracked work.

## Accuracy status

- Functional accuracy: not yet implemented.
- Architectural accuracy: not yet implemented.
- Timing accuracy: not yet implemented.
- FPGA readiness: not yet assessed.
