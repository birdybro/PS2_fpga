# R5900 Functional Foundation

Phase 2 begins with a deliberately single-issue, multi-cycle R5900 model. The
goal is architecturally observable correctness and fast diagnosis, not the
Emotion Engine's eventual dual-issue pipeline timing.

## Evidence boundary

The public DATE 2001 paper by Sony Computer Entertainment and Toshiba
establishes the Emotion Engine's high-level 128-bit, two-way superscalar CPU
organization and its relationship to the vector units and system blocks. The
publicly archived *MIPS IV Instruction Set, Revision 3.2* supplies base
user-mode instruction formats, encoding tables, operation pseudocode, and
documented exceptions. GNU Binutils R5900 target review records that the R5900
is not a drop-in complete MIPS III or MIPS IV processor and calls out subset and
FPU differences.

These sources have different authority. The MIPS manual may establish the base
semantics of a corroborated scalar instruction, but it cannot establish an
R5900-specific opcode, 128-bit destination extension, unsupported instruction,
COP0 rule, or FPU result. Toolchain discussion can identify behaviors requiring
research, but it is not hardware-semantics proof. The proprietary EE Core user
manual, leaked documentation, BIOS images, and proprietary SDK material are not
inputs to this clean reimplementation.

The first instruction set therefore contains only common scalar operations
selected for isolated verification. Every instruction milestone must record the
evidence for its exact R5900 encoding, affected GPR width, extension rule, and
exception behavior before its coverage entry can become implemented. Unknowns
remain pending rather than inheriting generic MIPS behavior silently.

## Initial architectural state

The timing-free Python reference state contains 32 general-purpose registers
with 128-bit storage, an immutable all-zero GPR 0, and a 32-bit program counter.
It is a frozen snapshot: computed GPR and PC updates return a new value and mask
Python integers explicitly to the architectural width. Its validated initial
PC rejects out-of-range loader input rather than silently truncating it.

The functional RTL will separately expose the current 32-bit instruction,
multi-cycle control state, reserved-instruction status, and one centralized GPR
writeback event as those milestones arrive. Its type package already fixes a
4096-bit packed GPR file, a 32-bit PC, a five-bit destination, and packed
writeback and reserved-instruction records. The debug interface exposes these
types through producer and monitor views, but does not implement storage. Those
timing and diagnostic fields do not belong in the reference model's
architectural snapshot. HI/LO-family state, COP0, exception entry, branches and
delay slots, data-memory operations, FPU, and MMI state are added only by later
granular roadmaps.

The first physical GPR storage block has two combinational read ports, one
synchronous write port, and a packed debug snapshot. It deliberately does not
initialize on reset: no consulted public R5900 source establishes post-reset
contents for GPR 1 through 31. A public R10000 implementation manual is recorded
only as a caution that generic MIPS logical registers need not reset to zero.
Tests therefore write all 32 physical locations before reading them. The
physical location at index zero remains writable until M048 adds the separate
architectural hardwired-zero boundary.

The architectural GPR wrapper now suppresses writes to index zero and forces
both read ports plus packed debug lane zero to 128 zero bits. A clocked
assertion makes this invariant fatal in required simulation. The underlying
physical-storage tests remain unchanged, keeping storage mechanics independent
from the architectural zero rule documented by both the MIPS IV notation and
PS2Tek's EE register description.

The functional PC register is 32 bits. While its active-low synchronous reset is
asserted it samples the harness-provided start address exactly, including values
that are not instruction-aligned; later fetch validation decides whether such an
address can execute. Redirect wins over sequential advance, advance adds four
modulo 32 bits, and otherwise the value holds. Loading an ELF entry point here
does not model the hardware reset vector or COP0 reset state.

The simulation loader's published ELF entry point supplies the initial PC for
early software tests. This is a harness start-address mechanism, not a claim
about the physical reset vector or COP0 reset behavior.

## Functional control sequence

The initial core permits one instruction in flight:

```text
FETCH_REQUEST -> FETCH_RESPONSE -> DECODE -> EXECUTE -> WRITEBACK
      ^                                                |
      +------------------------------------------------+
```

Requests and responses obey the existing single-outstanding ready/valid memory
contract. Fetch holds its complete request under backpressure and captures one
little-endian 32-bit instruction response before decode. Unsupported encodings
produce a diagnostic reserved-instruction event with the faulting PC and word;
architectural COP0 exception entry is a later milestone and must replace that
diagnostic through tested behavior.

The five control states are now a typed three-bit enum. Each state holds until
its corresponding completion event, advances to only its documented successor,
and returns from writeback to fetch-request. Reset enters fetch-request. A
reusable fatal checker rejects the remaining three enum values. The completion
inputs are functional boundaries for later modules, not fixed cycle latencies.

The fetch-request block now latches one aligned PC and issues one four-byte read
over the common memory interface. Address, direction, size, payload, and strobes
remain stable until the target accepts the request. A second start may replace
an accepted request in the same cycle, but cannot overwrite a request stalled
by backpressure. Assertions make unaligned starts and stalled replacement fatal.
This request block remains independent from response latency, error handling,
and instruction availability; the separate receiver owns those concerns.

The separate fetch-response block now arms on request acceptance and can accept
a target response in that cycle or after arbitrary latency. A one-entry register
captures response bits 31 through 0 as the instruction together with bus error
status, then holds both while the downstream decoder applies backpressure. The
complete response payload must be known. Unsolicited responses and a new request
while either a response or unconsumed instruction occupies the receiver are
fatal. Request, response, and control composition remains deferred to M079.

The next combinational boundary exposes instruction bits 31 through 26 as the
primary opcode; the three five-bit register indices; the five-bit shift amount;
the six-bit function; and the overlapping 16-bit immediate and 26-bit target.
It also supplies explicit 32-bit sign- and zero-extended immediate values. This
is format extraction only: no output identifies a legal R5900 instruction, and
the machine-readable ISA coverage therefore remains pending until instruction
admission and semantics pass their own milestones.

Decode admission is now explicit and closed by default. The initial five-bit
operation enum contains only no-operation and NOP, and the decoder selects NOP
only for exact word zero. Every other primary and SPECIAL encoding remains
illegal even if a later milestone plans it. This makes instruction support grow
only through independently verified admissions. NOP is therefore `decoded` and
`partial` in the coverage matrix, but remains unimplemented until M057 proves
its architectural state transition.

A decode-dispatch boundary now consumes that closed decoder. A valid admitted
word produces an execute-valid operation, while a valid unsupported word cannot
dispatch and instead produces the packed reserved-instruction diagnostic with
its exact PC and word. Inactive decode input produces neither output. Blocking
execute validity also blocks any later writeback eligibility, but this does not
yet model the architectural Reserved Instruction exception, EPC, Cause, Status,
or exception-vector PC transition; those remain COP0 milestones.

The functional sequence is not a pipeline model. Instruction latency, dual
issue, forwarding, hazards, cache timing, branch timing, and exception timing
remain explicitly inaccurate until later timing milestones.

## Verification contract

The Python model owns architectural state transitions without copying the RTL
state machine. RTL differential tests compare PC, all relevant 128-bit GPRs,
reserved-instruction state, and emitted writeback or trace events. Random cases
use deterministic seeds and emphasize zero, one, minus one, signed extrema,
all-one and alternating patterns, single bits, shift-mask boundaries, carry,
borrow, and immediate-extension boundaries.

Each instruction receives its own milestone with directed and randomized
differential coverage. `coverage/r5900_isa.yaml` tracks decode, implementation,
directed, randomized-differential, and exception coverage separately. Its 22
foundation entries start pending: an encoding string and milestone owner are a
plan, not an implementation claim. A validator cross-checks exact inventory,
roadmap ownership, reference provenance, and summary-state consistency. The
first integration gates fetch from the behavioral RAM, execute a sequential NOP
image, and then execute a generated EE ELF arithmetic stream from its published
entry point.

## Deferred behavior

The following are intentionally outside the first foundation roadmap:

- 64-bit scalar operations and R5900-specific 128-bit extension details not
  established by the initial instruction milestone;
- multiply, divide, HI/LO-family state, and known R5900 subset differences;
- jumps, branches, link behavior, branch-likely nullification, and delay slots;
- data loads and stores, alignment exceptions, and unaligned merge operations;
- architectural exceptions, COP0, interrupt entry, caches, and TLB behavior;
- COP1/FPU, COP2/VU0 macro mode, and MMI instructions;
- pipeline, dual-issue, hazard, and cycle accuracy.

Before each group begins, its documented functionality is enumerated into the
roadmap and coverage database using the same tested planning gate.
