# Progress

- Last completed milestone: M046 — define RTL R5900 architectural state types
- Next milestone: M047 — implement 128-bit R5900 GPR storage
- Current subsystem: R5900 general-purpose register storage
- Current regression status: 230 tests pass with no skips; RTL state package and both debug-interface modports compile and preserve widths
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M046 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. RTL types do not yet contain sequential state or
instruction semantics; resume with the single active milestone in
`milestones.yaml`.
