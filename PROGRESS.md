# Progress

- Last completed milestone: M005 — integrate pytest
- Next milestone: M006 — add top-level test runner
- Current subsystem: repository infrastructure
- Current regression status: pytest and cocotb each report 1 pass, 0 failures, 0 skips; build, regression, and bootstrap lint pass
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: no timing model exists
- External blockers: none
- Most recent pushed commit: M005 milestone commit (current `HEAD`; exact hash in `git log`)

## Resume note

The repository baseline was clean on `main`, matched `origin/main`, and had no
repository-local `AGENTS.md`. The configured remote is
`https://github.com/birdybro/PS2_fpga.git`. Verilator 5.050 and GNU Make 4.4.1
are installed. Cocotb and pytest are not installed globally and will be
provided through project-local tooling in later milestones.
