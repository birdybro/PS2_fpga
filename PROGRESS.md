# Progress

- Last completed milestone: M045 — define Python R5900 architectural state
- Next milestone: M046 — define RTL R5900 architectural state types
- Current subsystem: R5900 RTL state contracts
- Current regression status: 229 tests pass with no skips; immutable Python R5900 state passes width and boundary tests
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M045 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. The Python model currently contains state transitions
only, not instruction semantics; resume with the single active milestone in
`milestones.yaml`.
