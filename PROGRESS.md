# Progress

- Last completed milestone: M064 — implement R5900 LUI
- Next milestone: M065 — implement R5900 ORI
- Current subsystem: R5900 logical immediate execution
- Current regression status: 330 tests pass with no skips; LUI directed/reference checks and 517-case sequential randomized differential coverage are green
- Known architectural inaccuracies: only NOP, six 32-bit shifts, and LUI execute; reserved words emit diagnostics but do not enter COP0 exceptions
- Known timing inaccuracies: fetch uses functional ready/valid handshakes and a one-entry buffer; CPU pipeline, caches, and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M064 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architectural GPR, PC, functional control state, and
independently tested fetch request and response blocks now exist. Instruction
fields are extracted, exact zero-word NOP is admitted, and unsupported words are
blocked with diagnostic context. Exact zero-word NOP plus all six canonical
32-bit shift instructions plus LUI now execute, advance PC, and emit exact
retirement records; resume with the single active milestone in `milestones.yaml`.
