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

## Pytest orchestration

Pytest is the outer test orchestrator. A Python runner test builds Verilator,
launches cocotb, and independently checks the cocotb XML result for exactly one
executed test with no failures or skips. Cocotb remains the in-simulator test
manager. `make test` emits a separate pytest JUnit report, while `make unit`
selects the directed unit layer only.

## Top-level runner

`scripts/run_tests.py` is the single pytest entry point used by Make. It maps
named suites to strict pytest markers, forwards the deterministic seed and
isolated build root, writes JUnit results, and audits the report. A requested
suite fails when it collects zero tests or contains any failure, error, or skip.
