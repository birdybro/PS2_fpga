# Progress

- Last completed milestone: M047 — implement 128-bit R5900 GPR storage
- Next milestone: M048 — enforce immutable R5900 register zero
- Current subsystem: R5900 architectural general-purpose register file
- Current regression status: 231 tests pass with no skips; reset-free physical storage covers all 32 locations and both read ports
- Known architectural inaccuracies: physical GPR storage does not yet enforce hardwired register zero
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M047 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Physical GPR state now exists, but its architectural
zero-register wrapper and instruction semantics do not; resume with the single
active milestone in `milestones.yaml`.
