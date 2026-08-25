# Progress

- Last completed milestone: M023 — implement aligned 64-bit RAM reads
- Next milestone: M024 — implement aligned 64-bit RAM writes
- Current subsystem: behavioral system memory
- Current regression status: 57 tests pass with no skips; all aligned 64-bit reads match the byte-memory model
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: no PS2 architectural timing model exists
- External blockers: none
- Most recent pushed commit: M023 milestone commit (current `HEAD`; exact hash in `git log`)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
