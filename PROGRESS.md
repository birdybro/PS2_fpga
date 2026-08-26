# Progress

- Last completed milestone: M107 — implement R5900 DIV1
- Next milestone: M108 — implement R5900 DIVU1
- Current subsystem: R5900 multiply/divide execution
- Current regression status: M107 authoritative gate passes lint and all 748 tests with deterministic seed 1; zero failures, errors, or skips
- Known architectural inaccuracies: the 22-instruction scalar foundation plus twenty-three doubleword and dual-HI/LO operations execute; 9 extension operations remain pending, and branches, data memory, exceptions, and compiled C are absent
- Known timing inaccuracies: the core uses a deliberately functional five-state sequence, registered request handoff, and one-entry fetch buffer; pipeline, caches, and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M107 milestone commit (this commit)

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
in `milestones.yaml` to implement unsigned word division on the secondary HI1
and LO1 path with directed and randomized differential verification.
