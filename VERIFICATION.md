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

`make waves` builds the reusable simulation waveform control with Verilator
tracing enabled, runs its opt-in and disabled cases, and validates a changing
probe plus the VCD end-of-definitions marker. The intentionally retained,
ignored trace is written to `build/waves/sim_waveform_control/dump.vcd`.
Ordinary unit and regression runs delete their temporary enabled self-test VCD,
while the disabled case must not create a file even in a trace-capable binary.

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

## R5900 foundation roadmap validation

The Phase 2 foundation is a machine-checked linear sequence of 39 milestones:
coverage and reference state, RTL state and multi-cycle control, fetch/decode and
writeback, 22 separately gated scalar encodings, and three platform execution
tests. Directed mutation tests remove SRA and bypass its dependency to prove an
instruction cannot silently disappear or be bundled into a neighboring gate.
The planning document also separates base MIPS evidence from R5900-specific
behavior and defers unsupported or unproven ISA groups explicitly.

## R5900 ISA coverage validation

`coverage/r5900_isa.yaml` contains the exact 22-encoding foundation inventory in
roadmap order. Each entry names its milestone and cataloged evidence, and tracks
decode, implementation, directed testing, randomized differential testing, and
exception testing independently. Summary states cannot become `partial` or
`complete` unless their detailed fields justify the claim. Six directed
mutation tests prove that a missing or duplicate instruction, false completion,
wrong milestone owner, and unknown source all fail verification.

## R5900 architectural reference state

`reference/ee/r5900.py` defines a timing-free frozen state snapshot containing
32 explicitly bounded 128-bit GPRs and a 32-bit PC. A validated initializer
accepts the simulation loader's entry point without truncation. Computed GPR and
PC updates explicitly mask Python's unlimited integers, return a new snapshot,
and preserve all 128 bits of GPR zero. Thirty directed cases cover both width
boundaries, malformed snapshots, invalid types and indices, copy isolation,
every writable register, overflow normalization, and zero-register suppression.

## R5900 RTL state type contracts

The synthesizable package fixes GPR values at 128 bits, the packed 32-register
file at 4096 bits, GPR selectors at five bits, and PC/instruction values at 32
bits. Packed architectural-state, writeback, and reserved-instruction records
feed a debug interface with producer and monitor modports. Compile-time `$bits`
checks and two cocotb cases carry maximum-width asymmetric values through both
modports and lock GPR index zero to the low packed 128-bit lane. This verifies
types and observation only; no sequential storage behavior exists in M046.

RTL packages are ordered before other design units in the shared source list so
all top-level lint builds resolve imported types deterministically.

## R5900 physical GPR storage

The storage primitive contains 32 physical 128-bit locations, two independent
combinational reads, one rising-edge write, write-enable hold, and a packed
observation snapshot. Three cocotb cases write every location with asymmetric
full-width data, exercise both read ports, verify packed index mapping, preserve
state across disabled and unrelated edges, and distinguish pre-edge from
post-edge values. GPR zero is deliberately writable at this physical boundary;
M048 adds the architectural suppression wrapper without weakening these storage
tests.

No reset input initializes the array. The consulted public R5900 sources do not
define post-reset GPR contents, and the public R10000 manual demonstrates that
zero initialization is not a safe generic MIPS assumption. Every M047 test
writes a location before reading it.

## R5900 architectural GPR zero

The architectural wrapper blocks physical writes whose five-bit destination is
zero, independently forces either read port to 128 zero bits, and masks packed
debug lane zero. An assertion checks the 128-bit invariant on every rising edge.
Two cocotb cases observe zero before initialization, attempt zero, one, top-bit,
all-one, and alternating writes, combine zero with both read ports, initialize
all other locations, prove an attempted zero write cannot corrupt them, and
compare the complete packed architectural snapshot. The physical-storage suite
continues to test its writable index-zero location independently.

## R5900 program counter state

The standalone 32-bit PC loads an exact external start address synchronously
while reset is asserted, holds without control, increments by four with explicit
32-bit wraparound, and gives redirect priority over sequential advance. Four
cocotb cases cover zero, one, normal ELF, top-aligned, and all-one start values;
multi-edge hold; wrap to zero; repeated advance; aligned and unaligned redirect;
simultaneous redirect/advance; and reset resampling with highest priority. No
alignment or reset-vector rule is invented at this storage boundary.

## R5900 functional control states

The three-bit enum defines fetch-request, fetch-response, decode, execute, and
writeback states. Each state holds until its own completion input and advances
to exactly one successor; reset returns to fetch-request. Two legal cocotb cases
stall every state, traverse a complete loop, assert irrelevant completions,
exercise simultaneous events, and prove reset priority. A reusable assertion
checker is instantiated by the controller and rejects every value outside the
five-state set. A test-only second checker receives enum value seven and proves
the invariant terminates assertion-enabled simulation with the expected marker,
without forcing or multiply driving controller RTL.

## R5900 instruction-fetch requests

The request issuer latches one aligned 32-bit PC, emits an exact read with a
four-byte size code and zero write payload and strobes, and holds the complete
request while the target applies backpressure. Three legal cocotb cases cover
the lowest address, ordinary addresses, the final aligned 32-bit address,
source-PC changes during stalls, exactly one accepted handshake, and reset
cancellation. Two assertion-enabled negative runs prove that an unaligned
start and replacement of a stalled request terminate simulation with distinct
diagnostic markers. Strict standalone lint uses the request-only memory-bus
modport; response capture remains independently gated by M052.

## R5900 instruction-fetch responses

The one-entry response receiver arms only after an accepted fetch request,
accepts either a delayed or same-cycle response, validates the complete 128-bit
bus payload, and stores its low 32 bits with independent error status. Three
legal cocotb cases cover delayed handshake, low-word boundary patterns with
unrelated upper bits, downstream stalls and consumption, error preservation,
zero-wait response, and reset cancellation. Two assertion-enabled negative
runs prove that unsolicited responses and overlapping accepted fetch requests
are fatal. The response-only bus modport and standalone wrapper keep this gate
independent from later fetch/control composition.

## R5900 instruction-field extraction

The combinational field extractor exposes the standard overlapping 32-bit MIPS
format views without admitting or executing an opcode. Three directed cocotb
cases cover zero, all-one, alternating, and asymmetric words; isolate every
opcode, register, shift, and function bit range; and distinguish immediate
zero extension from signed boundaries at `0x7fff`, `0x8000`, and `0xffff`. A
separate randomized-layer test compares ten boundary words and 1,024 seeded
random words against independently expressed Python masks and arithmetic sign
extension. Coverage rows remain undecoded because field extraction alone does
not establish that any R5900 encoding is legal.

## R5900 decode admission skeleton

The initial combinational decoder admits exact word `0x00000000` as NOP and
reports every other word as no operation and illegal; this is admission, not
execution. Directed cocotb tests exhaust all 63 non-SPECIAL primary opcodes,
all 63 nonzero SPECIAL function codes, and nonzero register or shift fields
with zero function. A randomized-layer test independently applies the
word-equals-zero rule to eleven boundary encodings and 2,048 seeded arbitrary
words. The coverage matrix now marks NOP decode as partial while implementation
and semantic tests remain pending under M057.

## R5900 reserved-instruction diagnostics

The decode-dispatch boundary sends admitted operations toward execution and
maps every valid unsupported word to a packed diagnostic containing its exact
PC and instruction. Because execute validity remains low for that event, an
unsupported word cannot become eligible for the downstream writeback framework.
Three directed cocotb cases cover inactive-input masking, NOP dispatch without
a diagnostic, primary and SPECIAL failures, PC boundaries, opcode preservation,
and deterministic zeroing of inactive fields. A randomized-layer test compares
five boundary and 1,024 seeded validity/PC/word cases against an independent
dispatch rule. These diagnostics remain explicitly pre-architectural until
COP0 exception entry is implemented.

## R5900 architectural GPR writeback

The centralized writeback adapter consumes one destination/value commit per
asserted episode, produces a typed architectural event, and drives the existing
GPR file through matching enable, index, and 128-bit value signals. Four
directed cocotb cases cover zero, one, top-bit, all-one, alternating, and
asymmetric values; both read ports; accepted destination-zero suppression;
held-high payload changes; sampled-low rearming; and reset priority. The
randomized layer initializes every nonzero GPR, then independently models 512
seeded commit cycles and compares the complete 4,096-bit snapshot after each
edge. A fatal assertion independently prevents an emitted port write from ever
targeting GPR zero.

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

## Simulation cycle timeout

Four Verilator/cocotb cases cover disabled, first-cycle, and four-cycle watchdog
configurations plus the default fatal path. Observable cases verify the first
post-reset edge counts as one, timeout asserts exactly on configured cycle N,
the count saturates with sticky status, reset clears both outputs, and a zero
limit remains disabled across eight active edges. The fatal case requires
simulator failure at cycle three and checks the stable `SIM_TIMEOUT` message;
the test fails if simulation continues beyond the boundary.

## Simulation PASS termination

One cocotb case suppresses simulator exit and verifies reset-time PASS is
ignored, the first active request produces a one-cycle event and sticky status,
held and later requests do not retrigger, and reset re-arms exactly one new
event. A separate standalone Verilator binary exercises the default `$finish`
path, requires process status zero, and checks that exactly one `SIM_PASS`
marker appears while all fallback fatal messages remain absent.

## Simulation FAIL termination

One cocotb case suppresses terminal system tasks and exercises multiple reset
epochs. It verifies reset-time request suppression, exact 32-bit code capture,
one-cycle FAIL events, sticky failure, held/repeated-request suppression,
simultaneous FAIL-over-PASS priority, and first-terminal-result behavior in both
PASS-then-FAIL and FAIL-then-PASS orderings. A standalone Verilator binary drives
simultaneous requests through the default path and requires nonzero exit, one
coded `SIM_FAIL` marker, no `SIM_PASS`, and no fallback diagnostic.

## Memory transaction trace

Two Verilator/cocotb configurations run identical reset, stall, request,
response, simultaneous-handshake, and error stimulus. Disabled mode must not
create the requested file. Enabled mode is compared byte-for-byte against a
versioned five-line record: reset and stalls are absent, accepted operations
carry exact fixed-width payloads and active-cycle numbers, and the same-cycle
request precedes its response. The trace module also has its own strict
interface-aware Verilator lint top.

## Architectural event trace sink

Two Verilator/cocotb configurations apply the same reset-time event, inactive
gaps, and three payload-distinct active events. Disabled mode must not create a
file. Enabled mode is compared byte-for-byte against the versioned record
schema, including active-cycle numbers, zero-based contiguous sequence numbers,
source and kind tags, PC, instruction, identifier, and full 128-bit value.
Strict standalone Verilator lint covers the sink and its test wrapper.

## Composed simulation platform

The complete `ps2_sim_top` hierarchy is rebuilt with one-cycle and four-cycle
reset parameters. Directed cocotb stimulus holds valid memory, PASS, FAIL, and
architectural-event inputs throughout reset, then proves every reset-aware
output remains clear, RAM request readiness stays gated, and protocol state is
empty. Reset must release on the exact following falling edge; the valid RAM
request then becomes ready combinationally before being withdrawn ahead of the
first active rising edge. Three later edges remain idle. Disabled memory trace,
architectural trace, and waveform paths must create no requested files. A
dedicated whole-hierarchy Verilator lint invocation includes assertions.

## Raw binary platform integration

One integration test creates a deterministic 32-byte raw file only under the
ignored build root and loads it at address 32 into a 128-byte sentinel-filled
host image with `load_raw_binary_file`. The immutable range metadata is checked
before simulation. Cocotb independently reconstructs the expected host image,
initializes RTL RAM to the sentinel, overlays only the loaded half-open range
through the simulation backdoor, and reads boundary windows through the normal
memory transaction interface. Aligned 32-, 64-, and 128-bit reads cover the
first and second payload halves, bytes immediately before and after the load,
and the final legal 128-bit RAM window. Full 128-bit response comparison also
checks zero extension of narrower reads.

## EE ELF platform integration

One integration test independently encodes a temporary little-endian
`ET_EXEC`/`EM_MIPS` ELF32 image with two ordered `PT_LOAD` entries whose
physical addresses deliberately differ from their RAM destinations. The loader
must publish entry `0x00000044`, return exact segment metadata, copy 16 and 8
file bytes to virtual addresses `0x40` and `0xa0`, zero distinct 16- and 8-byte
BSS tails, and preserve a sentinel everywhere else. Cocotb reconstructs that
expected memory without calling the parser, initializes RTL RAM to the
sentinel, and overlays only the returned complete segment ranges. Transaction
reads cover the entry instruction bytes, both file payloads, both BSS regions,
inter-segment gaps, adjacency, and the final legal 128-bit RAM window using all
three implemented transfer widths.

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
