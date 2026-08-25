# Progress

- Last completed milestone: M057 — implement R5900 NOP encoding
- Next milestone: M058 — implement R5900 SLL
- Current subsystem: R5900 32-bit shift-left logical semantics
- Current regression status: 253 tests pass with no skips; exact NOP directed/reference checks and 260-state randomized differential coverage are green
- Known architectural inaccuracies: only NOP executes; reserved words emit diagnostics but do not enter COP0 exceptions
- Known timing inaccuracies: fetch uses functional ready/valid handshakes and a one-entry buffer; CPU pipeline, caches, and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M057 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architectural GPR, PC, functional control state, and
independently tested fetch request and response blocks now exist. Instruction
fields are extracted, exact zero-word NOP is admitted, and unsupported words are
blocked with diagnostic context. Exact zero-word NOP now executes, advances PC,
and retires without GPR changes; resume with the single active milestone in
`milestones.yaml`.
