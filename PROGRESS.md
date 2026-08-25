# Progress

- Last completed milestone: M048 — enforce immutable R5900 register zero
- Next milestone: M049 — implement R5900 program counter state
- Current subsystem: R5900 program counter state
- Current regression status: 232 tests pass with no skips; GPR zero read write snapshot and assertion coverage is green
- Known architectural inaccuracies: R5900 execution has no program counter or instruction control yet
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M048 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. The architectural GPR file now exists, but program
counter and instruction semantics do not; resume with the single active
milestone in `milestones.yaml`.
