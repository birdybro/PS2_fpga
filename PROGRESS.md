# Progress

- Last completed milestone: M039 — integrate simulation waveform controls
- Next milestone: M040 — assemble simulation platform top
- Current subsystem: simulation platform integration
- Current regression status: 186 tests pass with no skips; trace-capable disabled simulation creates no VCD and make waves retains a validated opt-in capture
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M039 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
