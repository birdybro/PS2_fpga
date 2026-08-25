# Progress

- Last completed milestone: M043 — expand Phase 2 R5900 foundation roadmap
- Next milestone: M044 — establish R5900 ISA coverage matrix
- Current subsystem: R5900 ISA coverage infrastructure
- Current regression status: 193 tests pass with no skips; Phase 2 has 39 machine-checked granular R5900 foundation milestones
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M043 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
