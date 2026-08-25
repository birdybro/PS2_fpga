# Progress

- Last completed milestone: M052 — capture R5900 instruction fetch responses
- Next milestone: M053 — extract R5900 instruction fields
- Current subsystem: R5900 instruction field extraction
- Current regression status: 241 tests pass with no skips; one-entry fetch response capture, backpressure, error, and fatal traffic invariants are green
- Known architectural inaccuracies: fetch request and response blocks are not yet composed with control; instruction decode and execution are unimplemented
- Known timing inaccuracies: fetch uses functional ready/valid handshakes and a one-entry buffer; CPU pipeline, caches, and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M052 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architectural GPR, PC, functional control state, and
independently tested fetch request and response blocks now exist. Instruction
field extraction and semantics do not; resume with the single active milestone
in `milestones.yaml`.
