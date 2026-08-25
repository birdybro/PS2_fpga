# Progress

- Last completed milestone: M031 — load ELF PT_LOAD file segments
- Next milestone: M032 — apply ELF zero-fill segments
- Current subsystem: simulation loaders
- Current regression status: 164 tests pass with no skips; validated PT_LOAD file bytes copy atomically to p_vaddr
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M031 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
