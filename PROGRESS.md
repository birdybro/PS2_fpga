# Progress

- Last completed milestone: M044 — establish R5900 ISA coverage matrix
- Next milestone: M045 — define Python R5900 architectural state
- Current subsystem: R5900 Python architectural reference model
- Current regression status: 199 tests pass with no skips; 22 pending foundation encodings have validated coverage owners
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M044 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. The coverage baseline does not claim instruction
implementation; resume with the single active milestone in `milestones.yaml`.
