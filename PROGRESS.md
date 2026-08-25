# Progress

- Last completed milestone: M042 — add ELF loader and RAM integration test
- Next milestone: M043 — expand Phase 2 R5900 foundation roadmap
- Current subsystem: R5900 foundation planning
- Current regression status: 190 tests pass with no skips; Phase 1 raw and two-segment EE ELF images read back byte-exactly through the composed platform
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M042 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
