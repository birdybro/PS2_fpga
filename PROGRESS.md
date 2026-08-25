# Progress

- Last completed milestone: M030 — validate EE ELF machine and endianness
- Next milestone: M031 — load ELF PT_LOAD segments
- Current subsystem: simulation loaders
- Current regression status: 143 tests pass with no skips; EE target policy accepts only little-endian MIPS executables
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M030 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
