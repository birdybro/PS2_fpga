# Progress

- Last completed milestone: M035 — add simulation PASS termination
- Next milestone: M036 — add simulation FAIL termination
- Current subsystem: simulation control
- Current regression status: 178 tests pass with no skips; PASS is reset-aware one-shot and exits standalone simulation successfully
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M035 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
