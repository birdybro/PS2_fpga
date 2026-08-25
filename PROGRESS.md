# Progress

- Last completed milestone: M009 — add waveform generation
- Next milestone: M010 — add GitHub Actions CI
- Current subsystem: simulation and verification infrastructure
- Current regression status: trace-enabled unit test produces a validated VCD; full regression and strict lint pass with no skips
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: no timing model exists
- External blockers: none
- Most recent pushed commit: M009 milestone commit (current `HEAD`; exact hash in `git log`)

## Resume note

The repository baseline was clean on `main`, matched `origin/main`, and had no
repository-local `AGENTS.md`. The configured remote is
`https://github.com/birdybro/PS2_fpga.git`. Verilator 5.050 and GNU Make 4.4.1
are installed. Cocotb and pytest are not installed globally and will be
provided through project-local tooling in later milestones.
