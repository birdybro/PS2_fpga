# PS2_fpga

PS2_fpga is a clean-room, simulation-first SystemVerilog reimplementation of
the Sony PlayStation 2 architecture. Development proceeds through small,
independently verified milestones; architectural correctness and automated
verification come before timing accuracy or FPGA-specific optimization.

The project is at infrastructure level (Level 0). See [PROGRESS.md](PROGRESS.md)
for the exact resume point and [MILESTONES.md](MILESTONES.md) for completion
rules.

No PlayStation 2 BIOS, game image, proprietary SDK material, or other
copyrighted Sony binary belongs in this repository.

## Development commands

Run `make help` for the stable development command surface. Commands are made
executable milestone-by-milestone; an unavailable verification layer fails
with the milestone that introduces it rather than silently passing.

## License

MIT. See [LICENSE](LICENSE).
