# Progress

- Last completed milestone: M053 — extract R5900 instruction fields
- Next milestone: M054 — add R5900 decode legality skeleton
- Current subsystem: R5900 instruction decode admission
- Current regression status: 243 tests pass with no skips; directed and 1,034-word randomized instruction-field extraction are green
- Known architectural inaccuracies: field extraction exists but no encoding is admitted or executed; fetch and control blocks remain uncomposed
- Known timing inaccuracies: fetch uses functional ready/valid handshakes and a one-entry buffer; CPU pipeline, caches, and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M053 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architectural GPR, PC, functional control state, and
independently tested fetch request and response blocks now exist. Instruction
fields are extracted without assigning legality or semantics; resume with the
single active milestone in `milestones.yaml`.
