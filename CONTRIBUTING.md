# Contributing

Keep changes narrow and testable. Do not weaken an existing test to accommodate
broken RTL. Add regression coverage for every fixed bug, use explicit widths
and synthesis-oriented SystemVerilog under `rtl/`, and keep simulation-only
behavior under `sim/`.

Never commit BIOS files, game images, proprietary or leaked documentation,
tool outputs, waveforms, caches, or downloaded material with uncertain
redistribution rights.

Use milestone commit subjects such as:

```text
milestone(M023): implement R5900 ADDIU
```

Run `make lint` before every milestone commit. It treats Verilator warnings as
errors, checks and formats Python with Ruff, validates YAML, rejects whitespace
errors, and prevents generated or prohibited binary paths from being tracked.
