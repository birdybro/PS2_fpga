# Progress

- Last completed milestone: M080 — execute a sequential R5900 NOP image
- Next milestone: M081 — execute an R5900 arithmetic EE ELF
- Current subsystem: R5900 program-image execution integration
- Current regression status: 482 tests pass with no skips; four sequential NOPs complete exact five-state sequencing, transaction counts, PC retirement, and timeout-bound halt checks
- Known architectural inaccuracies: only straight-line scalar execution is integrated; reserved words emit diagnostics but do not enter COP0 exceptions
- Known timing inaccuracies: the core uses a deliberately functional five-state sequence, registered request handoff, and one-entry fetch buffer; pipeline, caches, and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M080 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architectural GPR, PC, functional control state, and
independently tested fetch request and response blocks now exist and are
composed against behavioral RAM behind an explicit simulation-platform owner
selection. The PC, five-state control, fetch, decode, execute, writeback, and
GPR blocks now form a functional core that retires a bounded sequential NOP
image. All 22 instructions in the scalar foundation execute in isolated tests;
resume with the single active milestone in `milestones.yaml` to run arithmetic
from a generated EE ELF entry point.
