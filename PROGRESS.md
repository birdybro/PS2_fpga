# Progress

- Last completed milestone: M034 — add simulation cycle timeout
- Next milestone: M035 — add simulation PASS termination
- Current subsystem: simulation control
- Current regression status: 176 tests pass with no skips; cycle watchdog has exact reset active-edge disabled and fatal behavior
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M034 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
