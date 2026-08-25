# Progress

- Last completed milestone: M081 — execute an R5900 arithmetic EE ELF
- Next milestone: M082 — expand the R5900 64-bit integer roadmap
- Current subsystem: R5900 64-bit integer planning
- Current regression status: 483 tests pass with no skips; generated EE ELF entry, 13 retirements, 12 writebacks, final GPR state, automatic trace, and deterministic PASS are green
- Known architectural inaccuracies: only the 22-instruction straight-line scalar foundation is integrated; branches, data memory, exceptions, and compiled C are absent
- Known timing inaccuracies: the core uses a deliberately functional five-state sequence, registered request handoff, and one-entry fetch buffer; pipeline, caches, and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M081 milestone commit (this commit)

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
in `milestones.yaml` to expand the 64-bit integer roadmap.
