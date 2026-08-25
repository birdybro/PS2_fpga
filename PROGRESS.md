# Progress

- Last completed milestone: M015 — add simulation clock driver
- Next milestone: M016 — add simulation reset sequencer
- Current subsystem: simulation clock and reset infrastructure
- Current regression status: 21 tests pass with no skips; simulation timing lint and full regression pass
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: no PS2 architectural timing model exists
- External blockers: none
- Most recent pushed commit: M015 milestone commit (current `HEAD`; exact hash in `git log`)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
