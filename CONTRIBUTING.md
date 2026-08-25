# Contributing

Keep changes narrow and testable. Do not weaken an existing test to accommodate
broken RTL. Add regression coverage for every fixed bug, use explicit widths
and synthesis-oriented SystemVerilog under `rtl/`, and keep simulation-only
behavior under `sim/`.

The normative RTL, interface, arithmetic, assertion, reference-model, and test
rules are in `docs/CONVENTIONS.md`. Stable rule IDs make review findings
unambiguous. `make lint` enforces universal RTL file hygiene, rejects test skip
and expected-failure mechanisms, and requires every implementation
`TODO-ACCURACY` annotation to have a path-specific `KNOWN_ISSUES.md` entry.

Never commit BIOS files, game images, proprietary or leaked documentation,
tool outputs, waveforms, caches, or downloaded material with uncertain
redistribution rights.

Use milestone commit subjects such as:

```text
milestone(M023): implement R5900 ADDIU
```

Run targeted tests, `make lint`, and `make regression` before every milestone
commit. Lint treats Verilator warnings as errors, checks and formats Python with
Ruff, validates YAML and project policy, rejects whitespace errors, and prevents
generated or prohibited binary paths from being tracked. No required test may
be skipped or expected to fail.
