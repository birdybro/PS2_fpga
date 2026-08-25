# Verification

Verification will use directed SystemVerilog/cocotb unit tests, independent
Python reference models, differential comparisons, deterministic randomized
tests, subsystem integration tests, and increasingly realistic software
execution. The authoritative pre-commit gate will be exposed as
`make regression`; routine development will use `make test`.

No executable verification infrastructure exists yet. It is introduced in
small Phase 0 milestones.

## Command contract

The top-level `Makefile` owns the developer interface. `make test` is the
routine gate and `make regression` is the authoritative pre-commit gate.
`make lint`, `make unit`, `make differential`, `make randomized`,
`make integration`, `make software`, and `make waves` remain distinct so each
verification layer can run independently. Pending layers fail explicitly until
their implementation milestone completes.

## HDL compilation smoke test

`make build` uses Verilator to translate and compile `register_en` into a C++
model archive under ignored `build/`. Warnings are errors. The tiny common
module gives later cocotb and lint milestones a synthesis-oriented DUT without
claiming that any PS2 architectural behavior is implemented.

## Cocotb smoke test

`make unit` creates an ignored `.venv`, runs cocotb with Verilator, and checks
synchronous reset, enabled write, and disabled hold behavior. The upstream
cocotb revision is pinned because the host uses Python 3.14 and no compatible
stable release is currently published. JUnit-style simulator results are kept
under ignored `build/results/`.
