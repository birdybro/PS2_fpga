# Progress

- Last completed milestone: M056 — add R5900 GPR writeback framework
- Next milestone: M057 — implement R5900 NOP encoding
- Current subsystem: R5900 NOP execution semantics
- Current regression status: 249 tests pass with no skips; centralized one-shot writeback and 512-cycle full-GPR randomized comparison are green
- Known architectural inaccuracies: reserved words emit diagnostics but do not enter COP0 exceptions; exact NOP is decoded but has no state-transition implementation
- Known timing inaccuracies: fetch uses functional ready/valid handshakes and a one-entry buffer; CPU pipeline, caches, and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M056 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architectural GPR, PC, functional control state, and
independently tested fetch request and response blocks now exist. Instruction
fields are extracted, exact zero-word NOP is admitted, and unsupported words are
blocked with diagnostic context. The centralized GPR writeback path is ready,
but execution semantics do not yet exist; resume with the single active
milestone in `milestones.yaml`.
