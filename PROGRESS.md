# Progress

- Last completed milestone: M050 — define R5900 multi-cycle control states
- Next milestone: M051 — issue R5900 32-bit instruction fetch requests
- Current subsystem: R5900 instruction fetch request path
- Current regression status: 235 tests pass with no skips; five functional control states and fatal invalid-state coverage are green
- Known architectural inaccuracies: R5900 PC initialization is a harness entry point, not physical reset-vector behavior
- Known timing inaccuracies: PC updates are functional only; CPU pipeline and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M050 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architectural GPR, PC, and functional control state
now exist, but fetch traffic and instruction semantics do not; resume with the
single active milestone in `milestones.yaml`.
