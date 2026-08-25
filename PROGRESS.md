# Progress

- Last completed milestone: M079 — integrate R5900 fetch with simulation RAM
- Next milestone: M080 — execute a sequential R5900 NOP image
- Current subsystem: R5900 multi-cycle execution integration
- Current regression status: 481 tests pass with no skips; fetch reset, ownership, exact RAM latency, endianness, backpressure, and repetition checks are green
- Known architectural inaccuracies: fetch is not yet connected to control, decode, execute, or writeback; reserved words emit diagnostics but do not enter COP0 exceptions
- Known timing inaccuracies: fetch uses functional ready/valid handshakes, a registered request handoff, and a one-entry buffer; CPU pipeline, caches, and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M079 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architectural GPR, PC, functional control state, and
independently tested fetch request and response blocks now exist and are
composed against behavioral RAM behind an explicit simulation-platform owner
selection. Instruction fields are extracted, exact zero-word NOP is admitted,
and unsupported words are blocked with diagnostic context. All 22 instructions
in the scalar foundation execute, advance PC, and emit exact retirement
records; resume with the single active milestone in `milestones.yaml`.
