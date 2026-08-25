# Progress

- Last completed milestone: M038 — add architectural trace sink
- Next milestone: M039 — integrate simulation waveform controls
- Current subsystem: simulation waveform observability
- Current regression status: 184 tests pass with no skips; memory and architectural traces are disabled by default and byte-deterministic when enabled
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: RAM latency is configurable but does not model physical RDRAM timing
- External blockers: none
- Most recent pushed commit: M038 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architecture implementation has not started; resume
with the single active milestone in `milestones.yaml`.
