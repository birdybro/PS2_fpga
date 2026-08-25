# Progress

- Last completed milestone: M014 — expand Phase 1 simulation-platform roadmap
- Next milestone: M015 — add simulation clock driver
- Current subsystem: simulation clock and reset infrastructure
- Current regression status: 20 tests pass with no skips; strict lint and Phase 1 roadmap validation pass
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: no timing model exists
- External blockers: none
- Most recent pushed commit: M014 milestone commit (current `HEAD`; exact hash in `git log`)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
