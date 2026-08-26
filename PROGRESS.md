# Progress

- Last completed milestone: M094 — implement R5900 DADDIU
- Next milestone: M095 — implement R5900 DADDU
- Current subsystem: R5900 64-bit arithmetic execution
- Current regression status: 599 tests pass with no failures, errors, or skips; full lint and regression gates pass
- Known architectural inaccuracies: the 22-instruction scalar foundation plus ten doubleword and dual-HI/LO operations execute; 22 extension operations remain pending, and branches, data memory, exceptions, and compiled C are absent
- Known timing inaccuracies: the core uses a deliberately functional five-state sequence, registered request handoff, and one-entry fetch buffer; pipeline, caches, and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M094 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architectural GPR, PC, functional control state, and
independently tested fetch request and response blocks now exist and are
composed against behavioral RAM behind an explicit simulation-platform owner
selection. The PC, five-state control, fetch, decode, execute, writeback, and
GPR blocks now form a functional core. A generated native EE ELF loads into
behavioral RAM, begins at its published entry, executes 13 straight-line words,
matches exact retirement, writeback, final GPR, and architectural trace state,
then reaches the simulator PASS latch. Resume with the single active milestone
in `milestones.yaml` to implement nontrapping 64-bit register addition,
`DADDU`, with directed and randomized differential verification.
