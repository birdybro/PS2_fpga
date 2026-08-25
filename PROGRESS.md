# Progress

- Last completed milestone: M012 — establish references and provenance infrastructure
- Next milestone: M013 — establish coding and verification conventions
- Current subsystem: repository infrastructure
- Current regression status: 13 tests pass with no skips; strict lint and provenance policy validation pass
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: no timing model exists
- External blockers: none
- Most recent pushed commit: M012 milestone commit (current `HEAD`; exact hash in `git log`)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
