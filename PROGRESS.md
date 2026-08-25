# Progress

- Last completed milestone: M041 — add raw binary platform integration test
- Next milestone: M042 — add ELF loader and RAM integration test
- Current subsystem: EE ELF and simulation RAM integration
- Current regression status: 189 tests pass with no skips; external raw-file placement reads back byte-exactly through 32/64/128-bit platform transactions
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M041 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
