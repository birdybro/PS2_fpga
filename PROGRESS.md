# Progress

- Last completed milestone: M004 — add cocotb smoke test
- Next milestone: M005 — integrate pytest
- Current subsystem: repository infrastructure
- Current regression status: cocotb unit test (1 pass, 0 fail, 0 skip), build, regression, and bootstrap lint pass
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: no timing model exists
- External blockers: none
- Most recent pushed commit: M004 milestone commit (current `HEAD`; exact hash in `git log`)

## Resume note

The repository baseline was clean on `main`, matched `origin/main`, and had no
repository-local `AGENTS.md`. The configured remote is
`https://github.com/birdybro/PS2_fpga.git`. Verilator 5.050 and GNU Make 4.4.1
are installed. Cocotb and pytest are not installed globally and will be
provided through project-local tooling in later milestones.
