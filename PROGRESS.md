# Progress

- Last completed milestone: M055 — report R5900 reserved instructions
- Next milestone: M056 — add R5900 GPR writeback framework
- Current subsystem: R5900 architectural GPR writeback
- Current regression status: 247 tests pass with no skips; reserved diagnostics and 1,029-case randomized dispatch suppression are green
- Known architectural inaccuracies: reserved words emit diagnostics but do not enter COP0 exceptions; exact NOP is decoded but not executed
- Known timing inaccuracies: fetch uses functional ready/valid handshakes and a one-entry buffer; CPU pipeline, caches, and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M055 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architectural GPR, PC, functional control state, and
independently tested fetch request and response blocks now exist. Instruction
fields are extracted, exact zero-word NOP is admitted, and unsupported words are
blocked with diagnostic context. Execution semantics do not yet exist; resume
with the single active milestone in `milestones.yaml`.
