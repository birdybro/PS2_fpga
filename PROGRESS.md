# Progress

- Last completed milestone: M029 — parse ELF32 identification and header
- Next milestone: M030 — validate EE ELF machine and endianness
- Current subsystem: simulation loaders
- Current regression status: 128 tests pass with no skips; generic ELF32 headers decode in both declared byte orders
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M029 milestone commit (current `HEAD`; exact hash in `git log`)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
