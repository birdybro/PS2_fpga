# Progress

- Last completed milestone: M040 — assemble simulation platform top
- Next milestone: M041 — add raw binary platform integration test
- Current subsystem: simulation loader and RAM integration
- Current regression status: 188 tests pass with no skips; composed platform elaboration and one/four-cycle reset integration are green
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M040 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
