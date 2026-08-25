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

## Static checks

`make lint` runs Verilator `-Wall` lint over synthesizable RTL, Ruff checks and
format validation over Python, yamllint over machine-readable state, Git
whitespace validation, and a tracked-file hygiene audit. All checks are fatal;
there is no warning-only lint path.

## Deterministic randomized tests

`make randomized` runs boundary-heavy randomized tests with default seed `1`.
Override it with `make randomized RANDOM_SEED=<integer>`; the same outer seed
reproduces cocotb's derived per-test seed. Assertions include the effective
cocotb seed and iteration. If a randomized, routine, or regression invocation
fails, the runner appends its outer seed to ignored
`build/results/failing-seeds.log` so a later run cannot erase the reproducer.

## Waveforms

`make waves` rebuilds the directed register test with Verilator tracing enabled,
runs it at the selected deterministic seed, and validates both a nonempty VCD
and its end-of-definitions marker. The ignored trace is written to
`build/waves/register_en/dump.vcd`. Normal test and regression targets do not
enable tracing.

## Differential smoke layer

`make differential` compares register RTL transitions against the independent
`reference/common/register_en.py` state model. The shared vector set includes
reset priority, disabled holds, and unsigned 32-bit boundary values. The model
uses an independently formulated tick function and masks values to its declared
width.

## Integration smoke layer

`make integration` builds a test-only two-stage hierarchy from two common
register instances. Its cocotb test checks reset fanout, nonblocking one-cycle
propagation, and upstream hold behavior. The pytest wrapper also verifies the
cocotb XML result and confirms that the requested deterministic seed reached
the simulator.

## Continuous integration

GitHub Actions runs in the official pinned Verilator 5.050 container with
Python 3.14 and pinned Python dependencies. CI executes lint, build, unit,
differential, randomized, integration, and full regression as separate fatal
steps. Actions are pinned to commit hashes and repository permissions are
read-only. `make ci` runs the same checks serially on a local machine, while
`scripts/check_ci_workflow.py` validates the workflow contract itself.

## Persistent-state validation

`make lint` validates `milestones.yaml` schema, IDs, statuses, dependency order,
commit references, and exactly one active milestone. It also cross-checks the
last complete, next active, and most recently pushed resume pointers in
`PROGRESS.md`. Directed unit tests prove stale progress and incomplete active
dependencies are rejected.

## Reference provenance validation

`make lint` validates the schema and clean-room policy in `references.yaml`,
requires public credential-free HTTPS source links, and cross-checks every
machine-readable source against a unique marker in `REFERENCES.md`. Directed
unit tests prove duplicate IDs, weakened prohibited-material policy, unsafe
URLs, and stale human documentation are rejected. Uncertain-license documents
remain link-only, while any future local cache is ignored by Git.

## Convention enforcement

`docs/CONVENTIONS.md` assigns stable identifiers to RTL, interface, arithmetic,
assertion, reference-model, verification, and milestone-gate rules. Lint checks
that contract, requires implicit nets to be disabled in RTL, rejects source-level
skip and expected-failure mechanisms, and cross-checks every implementation
`TODO-ACCURACY` marker against `KNOWN_ISSUES.md`. Directed tests prove each
failure mode remains fatal.

## Simulation clock

The simulation-only `sim_clock` model starts low and generates an equal-duty
clock at an explicit time-valued period. Its directed cocotb test measures the
initial rising edge, four complete periods, and the following falling edge at
1 ps precision. Strict lint covers simulation SystemVerilog separately with
Verilator timing enabled.
