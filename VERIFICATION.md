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

## Simulation reset

The simulation-only `sim_reset` model holds active-low reset for a positive,
parameterized rising-edge count. Its isolated test composes the clock and reset
models, verifies reset before the first edge, samples every asserted edge,
checks exact falling-edge release, and observes three additional stable cycles.

## Internal memory transaction interface

`memory_bus_if` separates initiator- and target-driven signals with explicit
modports. A test-only pair of bridges proves all request and response payload
bits cross in the intended direction, including 128-bit data, byte strobes,
size, error, and independent ready backpressure. This milestone defines
connectivity only; protocol assertions are the next independently gated step.

## Memory transaction protocol assertions

`memory_bus_protocol_checker` tracks the single outstanding transaction and
asserts supported size, request/response stability under backpressure, valid
retention, response causality, and no second outstanding request. The legal
traffic test covers stalls, encodings for 1 through 16 bytes, zero-latency
completion, and simultaneous response/new-request replacement. Seven negative
simulations each inject one violation, require a fatal simulator exit, and
check the unique assertion marker in the captured log.

## Behavioral system RAM storage

The simulation-first RAM test writes distinct patterns to the first, second,
penultimate, and final bytes of a 256-byte instance. It proves byte-exact
readback, explicit out-of-range reporting, zero-valued out-of-range reads,
rejected writes without address truncation aliases, persistence across reset,
and suppression of writes while reset is active. No bus transfer behavior is
implemented or claimed in this storage milestone.

## Aligned 32-bit behavioral RAM reads

The directed read test initializes endian-asymmetric words at the first,
interior, and final aligned addresses, then checks registered responses, zeroed
upper bits, response backpressure, and rejection of unsupported request classes.
An independent Python model uses `bytearray` slicing and `int.from_bytes`, with
unit coverage for its bounds and alignment errors. Differential simulation
initializes all 256 bytes to a non-symmetric deterministic pattern and compares
every aligned 32-bit word against that model.

## Aligned 32-bit behavioral RAM writes

The directed write test covers first, interior, and final words with asymmetric
data, byte-by-byte backdoor inspection, architectural readback, response
backpressure, and rejection of partial strobes, wrong sizes, misalignment, and
out-of-range addresses. The Python model decomposes words with `int.to_bytes`
and validates address and value domains. Differential simulation writes every
aligned word through the RTL bus, then reads and compares the complete RAM image
against the independent model.

## Behavioral RAM 32-bit byte enables

The directed test resets a four-byte baseline before each of all 16 strobe
patterns, performs one bus write, and inspects every byte lane. It also covers
first/final word lane boundaries and rejects any upper strobe bit. The Python
model validates the same complete strobe domain using independent bytearray
updates. Differential simulation applies all masks repeatedly across the RAM
and compares every resulting word, including zero-strobe preservation.

## Behavioral RAM aligned 64-bit reads

The directed test reads the first, an interior, and the final legal aligned
doubleword with asymmetric byte patterns. It checks little-endian assembly,
zero-filled upper response bits, response stability under backpressure,
alignment, bounds, and rejection of 64-bit writes reserved for M024. The Python
model independently uses bounded byte slices and `int.from_bytes`; differential
simulation compares every aligned doubleword after initializing the complete
RAM image.

## Behavioral RAM aligned 64-bit writes

The directed test resets an asymmetric eight-byte baseline for each of all 256
legal byte-enable masks, verifies disabled-lane preservation, exercises both RAM
boundaries, stalls one completion response, and rejects upper strobe lanes. The
Python model independently updates a bytearray from `int.to_bytes` and validates
address, value, and strobe domains. Differential simulation distributes every
mask over repeated writes to all aligned doublewords, then compares the complete
RAM image through 64-bit bus reads.

## Behavioral RAM aligned 128-bit reads

The directed test reads the first, an interior, and the final legal aligned
quadword using hardcoded asymmetric endian vectors. It checks full-width response
stability under backpressure, alignment, bounds, and rejection of 128-bit writes
reserved for M026. The Python model independently forms bounded 16-byte slices
with `int.from_bytes`; differential simulation compares every aligned quadword
after initializing the complete RAM image.

## Behavioral RAM aligned 128-bit writes

The directed test covers every one-hot and one-cold lane mask, zero/full and
alternating interactions, both RAM boundaries, malformed addresses, and a
stalled completion response. The Python model independently validates address,
value, and strobe domains and exhaustively checks all 65,536 masks against byte
selection. Differential simulation uses same-cycle response consumption to
efficiently issue every 16-bit strobe pattern through the RTL, then compares the
complete RAM image through 128-bit reads.

## Behavioral RAM configurable response latency

One directed cocotb scenario is rebuilt at zero, one, and three inserted wait
cycles. It verifies the exact first `rsp_valid` edge for reads and writes,
request blocking while a response is pending, response stability under
backpressure, acceptance-time read-data capture despite a later backdoor change,
write side effects at acceptance, and reset cancellation of a pending response.
The complete existing RAM suite runs at the default zero setting to guard
backward compatibility.

## Raw binary loader

Fourteen directed Python cases cover bytes, bytearray, and memoryview inputs at
the first, interior, and final legal destinations; an empty image at the
exclusive upper bound; negative, past-end, and crossing ranges; invalid argument
types; explicit temporary-file loading; oversize files; and missing paths. Every
rejected range is checked for zero partial mutation, while valid loads verify
all surrounding bytes and returned half-open range metadata. Ruff now includes
`sim/` so loader code participates in the authoritative lint gate.

## Generic ELF32 header parser

Twenty-eight directed cases construct headers with an independent
integer-to-byte fixture builder. They decode every fixed field in little- and
big-endian headers with trailing data, verify reserved identification padding is
ignored, and independently reject truncation before 16 and 52 bytes, corruption
of each magic byte, non-ELF32 classes, invalid data encodings, invalid
identification and header versions, incorrect declared header sizes, and
non-bytes input.

## EE ELF32 target validation

Fifteen directed cases place a target-policy layer over the generic parser.
They accept little-endian `ET_EXEC`/`EM_MIPS` images, verify validation preserves
the immutable parsed record, and reject representative non-executable object
types, non-MIPS machine values, big-endian MIPS headers, and an invalid API input
domain. A separate case varies OS ABI, ABI version, and processor flags to
ensure the validator does not silently impose undocumented restrictions.

## ELF32 program headers and file-backed segments

Twenty-one directed cases use independent integer-to-byte encoders for the
fixed program-header table. They decode every field in both generic byte orders;
reject incorrect entry sizes, truncated tables, and ELF32 table overflow; and
accept an explicitly empty table. EE loading cases prove that `PT_LOAD` data is
copied to `p_vaddr` even when `p_paddr` differs, non-load entries are ignored,
gaps and future zero-fill bytes remain untouched, and returned range metadata is
exact. Negative cases cover EOF and RAM crossings, 32-bit source and destination
overflow, a malformed later segment, `p_filesz > p_memsz`, invalid alignment,
address incongruence, out-of-order entries, full-memory-range overlap, and an
invalid destination type. Every rejected multi-segment image is checked for no
partial mutation.

## ELF32 memory-only segment tails

Four directed cases exercise the complete EE segment API above the file-only
loader. They verify initialized data followed by zero-filled BSS, a BSS-only
segment, preservation of gaps and bytes adjacent to equal-sized file/memory
segments, and a zero-fill tail ending exactly at the exclusive RAM boundary. A
multi-segment malformed-size case proves `p_filesz > p_memsz` is rejected before
any earlier file copy or BSS clear.

## ELF32 entry-point publication

Four directed cases load complete images and propagate representative `e_entry`
values of zero, the normal EE software base, and all ones without truncation or
invented segment-membership policy. Each case also verifies initialized data,
BSS, and returned segment metadata. The remaining case proves the completed
image result is immutable so its published start address cannot drift after
load.
