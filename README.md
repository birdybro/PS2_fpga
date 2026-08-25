# PS2_fpga

PS2_fpga is a clean-room, simulation-first SystemVerilog reimplementation of
the Sony PlayStation 2 architecture. Development proceeds through small,
independently verified milestones; architectural correctness and automated
verification come before timing accuracy or FPGA-specific optimization.

The project has completed Level 0 infrastructure and the Phase 1 simulation
platform: behavioral RAM, raw and EE ELF loading, deterministic termination,
tracing, waveforms, and platform integration are verified. R5900 execution
(Level 1) is not implemented yet. See [PROGRESS.md](PROGRESS.md) for the exact
resume point and [MILESTONES.md](MILESTONES.md) for completion rules.

No PlayStation 2 BIOS, game image, proprietary SDK material, or other
copyrighted Sony binary belongs in this repository.

## Development commands

Run `make help` for the stable development command surface. Commands are made
executable milestone-by-milestone; an unavailable verification layer fails
with the milestone that introduces it rather than silently passing.

`make test` runs the routine pytest suite. `make regression` runs the
authoritative pre-commit suite. Set `RANDOM_SEED=<integer>` to reproduce seeded
verification; the default is `1`.

## License

MIT. See [LICENSE](LICENSE).
