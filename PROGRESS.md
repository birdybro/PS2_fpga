# Progress

- Last completed milestone: M008 — add deterministic randomized-test infrastructure
- Next milestone: M009 — add waveform generation
- Current subsystem: repository infrastructure
- Current regression status: randomized seeds 1 and 305419896 pass; full regression and strict lint pass with no skips
- Known architectural inaccuracies: all PS2 architecture is unimplemented
- Known timing inaccuracies: no timing model exists
- External blockers: none
- Most recent pushed commit: M008 milestone commit (current `HEAD`; exact hash in `git log`)

## Resume note

The repository baseline was clean on `main`, matched `origin/main`, and had no
repository-local `AGENTS.md`. The configured remote is
`https://github.com/birdybro/PS2_fpga.git`. Verilator 5.050 and GNU Make 4.4.1
are installed. Cocotb and pytest are not installed globally and will be
provided through project-local tooling in later milestones.
