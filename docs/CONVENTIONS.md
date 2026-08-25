# Coding and Verification Conventions

These rules apply to new work and to modified legacy code. Exceptions require
a documented technical reason, a narrowly scoped lint waiver when unavoidable,
and review in the milestone diff.

## RTL coding rules

- [RTL-001] Synthesizable design code belongs under `rtl/`; testbench-only
  behavior belongs under `sim/` or `tests/`.
- [RTL-002] Use SystemVerilog `logic`, explicit packed widths, sized literals,
  and typed parameters. Each RTL file must disable implicit nets with
  `` `default_nettype none `` and restore the tool default at the end.
- [RTL-003] Use `always_ff` with nonblocking assignments for sequential state.
  Use `always_comb` with blocking assignments and complete defaults for
  combinational logic. Inferred latches and combinational feedback are defects
  unless an architecture-specific exception is documented and tested.
- [RTL-004] Use enums for nontrivial state machines and make illegal states
  observable through assertions. Keep modules narrow enough for isolated unit
  tests and avoid vendor primitives in architectural RTL.
- [RTL-005] Every source file carries an SPDX license identifier. Comments
  explain architectural intent, ordering, or a non-obvious constraint rather
  than paraphrasing syntax.

## Interface and reset rules

- [IFC-001] Ports use `_i`, `_o`, or `_io`; clocks use `clk_`, active-low resets
  use `rst_n`, and module instances use `u_`. Ready/valid interfaces hold data
  stable while valid is asserted and ready is deasserted.
- [IFC-002] Reset polarity and synchronous or asynchronous behavior are explicit
  in each interface. Architectural state receives a deterministic reset when
  the hardware specifies one; unknown hardware power-up state is not silently
  replaced with a convenient value.
- [IFC-003] Multi-byte interfaces state their transfer width, address unit, byte
  enables, alignment, and backpressure behavior. A handshake transfers exactly
  once on a cycle in which both ready and valid are asserted.

## Arithmetic and data-layout rules

- [DAT-001] Signedness is intentional at every arithmetic, comparison,
  extension, and shift boundary. Use explicit `$signed` or `$unsigned` casts and
  intermediate widths where SystemVerilog expression sizing could truncate or
  reinterpret a value.
- [DAT-002] Unless a documented interface says otherwise, bit 0 is the least
  significant bit, byte lane 0 is bits 7:0, and increasing byte addresses map
  to increasing packed byte lanes. Tests must include lane and endianness
  patterns rather than only symmetric values.
- [DAT-003] Python models mask results to architectural widths and explicitly
  implement sign extension, wraparound, division edge cases, and shift-count
  rules. Python's unlimited integers must not become accidental extra precision.

## Assertions and accuracy annotations

- [AST-001] Add assertions for useful invariants such as immutable register
  zero, FIFO bounds, one-hot grants, legal writeback destinations, and valid
  state transitions. Assertions are fatal in required simulation.
- [AST-002] Any deliberate functional or timing approximation is marked
  `TODO-ACCURACY`, documented in `KNOWN_ISSUES.md` with its source path and
  impact, and assigned a replacement milestone. Absence of an annotation is not
  evidence of accuracy; claims require tests.
- [AST-003] Simulation debug and tracing mechanisms must be switchable and must
  not alter architectural state or leak into synthesizable interfaces.

## Reference-model rules

- [REF-001] Reference models prioritize clarity and architectural state over
  timing. They do not copy the RTL's control structure merely to reach the same
  result.
- [REF-002] Differential checks compare every relevant visible state field and
  explicitly classify undefined or implementation-specific fields instead of
  inventing expected values.
- [REF-003] Significant technical inputs are registered in `references.yaml`
  before use. Source-code consultation and uncertain behavior follow the policy
  in `REFERENCES.md`.

## Verification rules

- [VER-001] Directed tests cover the nominal behavior and boundary cases.
  Differential and randomized tests are required when a clear independent
  model is practical; integration tests cover handshakes and backpressure.
- [VER-002] Boundary vectors aggressively include zero, one, minus one, extrema,
  all ones, alternating bits, single bits, carry and overflow boundaries,
  alignment boundaries, and representative byte-lane patterns.
- [VER-003] Randomized tests use an explicit reproducible seed and include the
  seed and iteration in failures. Iteration counts are reduced only for an
  independently justified performance budget, never to conceal a defect.
- [VER-004] Required tests may not use skip, xfail, warning-only assertions, or
  expected-failure switches. A genuinely incorrect test is changed only with
  cited architectural evidence and replacement coverage.
- [VER-005] A bug fix first gains a focused regression that fails for the
  original cause. Tests must not share an implementation formulation that can
  duplicate the RTL bug unnoticed.

## Review and milestone gate

- [GATE-001] A milestone is one narrow behavior. Before commit, run its targeted
  tests, `make lint`, and the full `make regression` gate with no skipped tests.
- [GATE-002] Review reset behavior, signedness, widths, truncation, shifts,
  nonblocking update order, byte enables, endianness, state reachability, and
  whether tests exercise more than the happy path.
- [GATE-003] Update documentation, `milestones.yaml`, and `PROGRESS.md`; inspect
  `git diff`, `git status`, and tracked-file hygiene; then commit and push. A
  remote CI failure receives an additive fix rather than rewritten history.
