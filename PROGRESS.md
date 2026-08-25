# Progress

- Last completed milestone: M020 — implement aligned 32-bit RAM reads
- Next milestone: M021 — implement aligned 32-bit RAM writes
- Current subsystem: behavioral system memory
- Current regression status: 39 tests pass with no skips; directed and exhaustive differential read32 gates pass
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: no PS2 architectural timing model exists
- External blockers: none
- Most recent pushed commit: M020 milestone commit (current `HEAD`; exact hash in `git log`)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
