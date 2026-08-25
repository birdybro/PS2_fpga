# Progress

- Last completed milestone: M051 — issue R5900 32-bit instruction fetch requests
- Next milestone: M052 — capture R5900 instruction fetch responses
- Current subsystem: R5900 instruction fetch response path
- Current regression status: 238 tests pass with no skips; aligned 32-bit fetch requests and fatal request invariants are green
- Known architectural inaccuracies: fetch responses and the instruction register are not yet implemented; R5900 PC initialization remains a harness entry point
- Known timing inaccuracies: fetch uses only functional ready/valid handshakes; CPU pipeline, caches, and physical RDRAM timing are unmodeled
- External blockers: none
- Most recent pushed commit: M051 milestone commit (this commit)

## Resume note

Development is on `main` with remote
`https://github.com/birdybro/PS2_fpga.git`. The pinned local environment uses
Verilator 5.050, Python 3.14, cocotb, and pytest. `make ci` is the complete
local verification gate. Architectural GPR, PC, functional control state, and
the fetch-request issuer now exist. Fetch-response capture and instruction
semantics do not; resume with the single active milestone in `milestones.yaml`.
