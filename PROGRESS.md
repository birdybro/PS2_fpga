# Progress

- Last completed milestone: M054 — add R5900 decode legality skeleton
- Next milestone: M055 — report R5900 reserved instructions
- Current subsystem: R5900 reserved-instruction diagnostics
- Current regression status: 245 tests pass with no skips; exact NOP admission, exhaustive rejection, and 2,059-word randomized coverage are green
- Known architectural inaccuracies: exact NOP is decoded but not executed; unsupported encodings do not yet emit diagnostics or architectural exceptions
- Known timing inaccuracies: fetch uses functional ready/valid handshakes and a one-entry buffer; CPU pipeline, caches, and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M054 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architectural GPR, PC, functional control state, and
independently tested fetch request and response blocks now exist. Instruction
fields are extracted and only exact zero-word NOP is admitted, without execution
semantics; resume with the single active milestone in `milestones.yaml`.
