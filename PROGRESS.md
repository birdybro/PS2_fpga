# Progress

- Last completed milestone: M062 — implement R5900 SRLV
- Next milestone: M063 — implement R5900 SRAV
- Current subsystem: R5900 32-bit variable arithmetic shift-right semantics
- Current regression status: 310 tests pass with no skips; SRLV directed/reference checks and 521-case sequential randomized differential coverage are green
- Known architectural inaccuracies: only NOP, SLL, SRL, SRA, SLLV, and SRLV execute; reserved words emit diagnostics but do not enter COP0 exceptions
- Known timing inaccuracies: fetch uses functional ready/valid handshakes and a one-entry buffer; CPU pipeline, caches, and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M062 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architectural GPR, PC, functional control state, and
independently tested fetch request and response blocks now exist. Instruction
fields are extracted, exact zero-word NOP is admitted, and unsupported words are
blocked with diagnostic context. Exact zero-word NOP plus canonical SLL, SRL,
SRA, SLLV, and SRLV now execute, advance PC, and emit exact retirement records;
resume with the single active milestone in `milestones.yaml`.
