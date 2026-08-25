# Progress

- Last completed milestone: M049 — implement R5900 program counter state
- Next milestone: M050 — define R5900 multi-cycle control states
- Current subsystem: R5900 functional multi-cycle control
- Current regression status: 233 tests pass with no skips; 32-bit PC start hold advance wrap redirect and priority coverage is green
- Known architectural inaccuracies: R5900 PC initialization is a harness entry point, not physical reset-vector behavior
- Known timing inaccuracies: PC updates are functional only; CPU pipeline and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M049 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architectural GPR and PC state now exist, but CPU
control and instruction semantics do not; resume with the single active
milestone in `milestones.yaml`.
