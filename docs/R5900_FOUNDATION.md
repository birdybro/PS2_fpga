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

PS2Tek independently identifies SLL in the EE SPECIAL function table. A public
QEMU R5900 architecture overview states that GPR bits 127:64 are used only by
quadword transfers and selected multimedia operations. After explicit GPL-3.0
license review, the PCSX2 interpreter was consulted only to corroborate scalar
width rules, including MULT/MULTU's signed or unsigned low-word operands,
independently sign-extended product halves, optional low-64-bit destination
write, DIV's R5900 overflow and zero-divisor results, and DIVU's result extension
and zero-divisor behavior. A separately reviewed BSD-licensed Play!
implementation independently corroborates both divide operations' edge rules;
a public Linux report from actual R5900 hardware corroborates the common
nonnegative divide-by-zero quotient. PCSX2 and Play! also corroborate MFHI's
and MFLO's complete 64-bit primary-HI or primary-LO transfer into the low GPR
scalar lane. No emulator
source text or implementation structure is copied.

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

## 64-bit integer and dual-HI/LO roadmap

M082 expands the next functional integer boundary into 36 independently gated
milestones. The machine-readable ISA matrix now owns 32 additional encodings:

- immediate doubleword shifts: `DSLL`, `DSRL`, `DSRA`, `DSLL32`, `DSRL32`,
  and `DSRA32`;
- variable doubleword shifts: `DSLLV`, `DSRLV`, and `DSRAV`;
- nontrapping doubleword arithmetic: `DADDIU`, `DADDU`, and `DSUBU`;
- primary multiply/divide and transfers: `MULT`, `MULTU`, `DIV`, `DIVU`,
  `MFHI`, `MFLO`, `MTHI`, and `MTLO`;
- secondary-path equivalents: `MULT1`, `MULTU1`, `DIV1`, `DIVU1`, `MFHI1`,
  `MFLO1`, `MTHI1`, and `MTLO1`; and
- multiply-accumulate operations: `MADD`, `MADDU`, `MADD1`, and `MADDU1`.

PS2Tek's SPECIAL and MMI tables establish the R5900-specific inclusion and
encodings, while the public MIPS IV manual supplies base semantics where the
operation is shared. GNU assembler opcode and encoding tests independently
corroborate the inventory, including optional `rd` forms for R5900 multiply and
multiply-accumulate instructions. The QEMU R5900 overview corroborates the
separate pipeline-1 operation set. These sources are recorded with consultation
and license metadata in `references.yaml`.

Generic MIPS III/IV `DMULT`, `DMULTU`, `DDIV`, and `DDIVU` are deliberately not
in the R5900 roadmap: their SPECIAL function positions are absent in the
R5900-specific table, and the GNU target excludes them. Conversely, trapping
`DADDI`, `DADD`, and `DSUB` are documented R5900 encodings but are deferred to
the exception roadmap so they cannot be implemented as silently nontrapping
operations. Branch and jump expansion begins only after the planned
doubleword/dual-HI/LO integration gate.

The roadmap does not turn uncertain behavior into a specification. The
optional-`rd` result and destination-width rules must be corroborated during
each corresponding multiply milestone; M097 and M098 resolve that boundary for
the primary MULT and MULTU pair only. M099 and M100 resolve result extension,
overflow, and divide-by-zero behavior for primary DIV and DIVU; secondary-path
divide operations remain pending their own evidence gates.
Post-reset values of the four 64-bit `HI`, `LO`, `HI1`, and `LO1` registers are
also unproven, so M084 must not invent a reset value.

## Initial architectural state

The timing-free Python reference state contains 32 general-purpose registers
with 128-bit storage, an immutable all-zero GPR 0, a 32-bit program counter,
and four independent 64-bit multiply/divide registers named `HI`, `LO`, `HI1`,
and `LO1`. It is a frozen snapshot: computed GPR, PC, and HI/LO-family updates
return a new value and mask Python integers explicitly to the architectural
width. Its validated initializer rejects out-of-range loader and multiply-
divide state rather than silently truncating external input.

The initializer accepts an explicit value for each multiply/divide register;
its zero defaults provide deterministic test setup only and are not an R5900
reset claim. Direct snapshots require already normalized unsigned values, while
the four computed-result methods mask unlimited Python integers to 64 bits.
Every existing GPR, PC, and instruction successor preserves all four registers.

The synthesizable `r5900_hilo_state` block mirrors those four 64-bit fields with
independent synchronous write enables and individual plus packed observation
outputs. It intentionally has no reset input or initialization construct. The
testbench writes all four registers before reading any of them, so deterministic
simulation does not become an unsupported hardware-reset claim. All four writes
may commit on the same edge, while disabled fields retain their prior value.
Primary HI/LO writes are now connected to the functional core for MULT, MULTU,
DIV, DIVU, MTHI, and MTLO. HI1 and LO1 remain isolated until the secondary-path
instruction milestones. MFHI and MFLO read primary HI and LO respectively
without modifying any accumulator field; MTHI replaces only primary HI from a
GPR's low 64-bit scalar lane, and MTLO applies the same rule to primary LO.

The functional RTL separately exposes the current 32-bit instruction,
multi-cycle control state, reserved-instruction status, and one centralized GPR
writeback event as those milestones arrive. Its type package already fixes a
4096-bit packed GPR file, a 32-bit PC, a five-bit destination, and packed
writeback and reserved-instruction records. The debug interface exposes these
types through producer and monitor views, but does not implement storage. Those
timing and diagnostic fields do not belong in the reference model's
architectural snapshot. The RTL type package now includes a 256-bit packed
HI/LO-family state inside the architectural snapshot; COP0, exception entry,
branches and delay slots, data-memory operations, FPU, and the remaining MMI
state are added only by later granular roadmaps.

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

M079 composes those request and response halves as one synthesizable fetch
path and selects it as the simulation platform's memory initiator. Request
acceptance crosses a register before arming response state, removing a
combinational readiness path through a zero-latency target while retaining the
receiver's standalone same-cycle capability. Start readiness stays low for a
pending request, the registered acceptance handoff, an expected response, or
an unconsumed instruction. Integration verification fetches two distinct
little-endian words from behavioral RAM with configured two-cycle latency,
holds each buffered word under backpressure, and proves that the disabled
external memory-master inputs cannot alter the transaction stream.

M080 adds the first complete functional core composition. The existing
five-state controller now gates fetch, captures one response word for decode,
latches the admitted operation for execute, captures execute outputs, and
publishes retirement during writeback. PC advances only when execute completes;
GPR commits occur from the following writeback state. A synthesis-compatible
run input prevents only new fetches so simulation can initialize RAM and stop
cleanly between instructions. Four loaded NOP words traverse the complete
state loop, retire at consecutive PCs, perform no register writes, and stop at
the first address beyond the bounded image.

M081 uses the established EE loader rather than a direct word fixture. A
generated executable segment places one valid but deliberately skipped
instruction before its published entry, followed by LUI, logical immediates,
wrapping word arithmetic, signed and unsigned comparisons, NOR, and NOP. The
core retires the 13-word stream, commits 12 exact GPR updates from writeback,
preserves upper 64-bit destination lanes, leaves the skipped destination and
GPR zero unchanged, and stops at the first PC beyond the program. Retirement
also drives the simulation architectural trace as EE source/kind `0x01`, and
the completed program pulses the deterministic PASS latch.

The next combinational boundary exposes instruction bits 31 through 26 as the
primary opcode; the three five-bit register indices; the five-bit shift amount;
the six-bit function; and the overlapping 16-bit immediate and 26-bit target.
It also supplies explicit 32-bit sign- and zero-extended immediate values. This
is format extraction only: no output identifies a legal R5900 instruction, and
the machine-readable ISA coverage therefore remains pending until instruction
admission and semantics pass their own milestones.

Decode admission is explicit and closed by default. The five-bit operation enum
contains no-operation, NOP, and all six 32-bit shift operations. Exact word zero selects the canonical
NOP alias; other SPECIAL function-zero words select SLL, while SPECIAL
function-two words select SRL, function-three words select SRA, and
function-`0x38` words select DSLL, function-`0x3a` words select DSRL, and
function-`0x3b` words select DSRA. Those
immediate shifts require reserved `rs` to be zero. Function-four words select
SLLV, function-six words select SRLV, and function-seven words select SRAV; all
require reserved `sa` to be zero. Every
other primary and SPECIAL encoding remains illegal even if a later milestone
plans it. This makes instruction support grow only through independently
verified admissions.

A decode-dispatch boundary now consumes that closed decoder. A valid admitted
word produces an execute-valid operation, while a valid unsupported word cannot
dispatch and instead produces the packed reserved-instruction diagnostic with
its exact PC and word. Inactive decode input produces neither output. Blocking
execute validity also blocks any later writeback eligibility, but this does not
yet model the architectural Reserved Instruction exception, EPC, Cause, Status,
or exception-vector PC transition; those remain COP0 milestones.

Architectural GPR updates now have one central adapter. A commit assertion is
accepted once, even if held across multiple edges; a sampled low cycle rearms
the next episode. Accepted destination zero is consumed without a GPR write or
architectural writeback event. Every nonzero event carries the exact five-bit
destination and 128-bit value that drive the GPR file, giving traces and future
differential tests one observation point. This functional episode protocol is
not a claim about the eventual EE pipeline retirement timing.

Exact word zero now has its full initial architectural transition. Decode and
dispatch select NOP, execution completes immediately at the functional boundary,
PC advances by four modulo 32 bits, and every GPR remains unchanged. No GPR
commit or writeback event occurs. A separate typed retirement record captures
the pre-advance PC and exact instruction for trace consumers. The Python model's
`step` method independently implements only this word and rejects all other
encodings, making NOP the first `complete` ISA coverage entry.

Canonical nonzero SLL now reads `rt[31:0]`, applies the immediate five-bit
shift, and truncates to a 32-bit word. Bit 31 is sign-extended through GPR bits
63:32, while the old destination's bits 127:64 are preserved. The central
writeback boundary suppresses a legal SLL targeting GPR zero; the exact
all-zero encoding remains NOP and issues no commit at all. Both aliasing
`rd == rt` and distinct source/destination forms read the original state before
the complete 128-bit destination is formed. The independent Python transition
and RTL executor now make SLL the second complete ISA coverage entry.

Canonical SRL uses the same destination merge after logically shifting
`rt[31:0]` right by the immediate count. Zeroes enter at the top of the word,
but the completed 32-bit word is still interpreted by the EE scalar destination
rule: a count of zero can therefore preserve bit 31 and produce ones in bits
63:32, while every nonzero count necessarily clears bit 31. Source bits 127:32
remain irrelevant and destination bits 127:64 remain intact. Directed and
randomized differential tests make SRL the third complete ISA coverage entry.

Canonical SRA treats `rt[31:0]` as a signed two's-complement word before the
immediate right shift. Negative words shift in ones and positive words shift
in zeroes. The resulting word is sign-extended through bits 63:32, while the
old destination bits 127:64 remain intact. Explicit signed RTL and independent
Python integer conversion cover counts 0, 1, 30, and 31, both source signs,
aliasing, GPR-zero suppression, PC wrap, and exact events. Sequential randomized
differential tests make SRA the fourth complete ISA coverage entry.

Canonical SLLV selects the runtime count exclusively from `rs[4:0]`; all other
count-register bits are ignored. It shifts `rt[31:0]` left, truncates to one
word, sign-extends that word through bits 63:32, and retains the old destination
bits 127:64. Counts 32, 33, and all ones explicitly prove modulo-32 masking.
Tests also cover `rd == rt`, `rd == rs`, destination zero, reserved `sa`, PC
wrap, and exact events. Nine boundary plus 512 sequential randomized cases make
SLLV the fifth complete ISA coverage entry.

Canonical SRLV uses the same masked runtime count and destination merge after
logically shifting `rt[31:0]` right. A raw count of zero can leave word bit 31
set, so the result is then sign-extended through bits 63:32. Any nonzero
effective count zero-fills bit 31 and therefore produces a nonnegative scalar
result. Tests separate these two stages while covering counts 0, 1, 30, and 31,
raw values 32, 33, and all ones, both alias directions, reserved `sa`, and exact
events. Nine boundary plus 512 randomized cases make SRLV the sixth complete
ISA coverage entry.

Canonical SRAV combines the masked variable count with signed-word arithmetic
shift behavior. The RTL reuses an explicitly signed source word, while the
Python model converts the masked unsigned word to a negative integer when bit
31 is set. Counts 0, 1, 30, and 31 cover both source signs; raw values 32, 33,
and all ones prove count masking. Alias, destination-zero, reserved-field, PC,
and event checks complete the directed layer. Nine boundary plus 512 randomized
cases make SRAV the seventh complete ISA coverage entry and complete the initial
32-bit shift family.

Canonical DSLL is the first implemented 64-bit shift. SPECIAL function `0x38`
requires reserved `rs` to be zero, reads only `rt[63:0]`, shifts left by the
encoded count from 0 through 31, and truncates the result to 64 bits. It does
not sign-extend a word: old destination bits 127:64 remain intact around the
new low doubleword. Directed checks cover counts 0, 1, 30, and 31, bit-63
generation and overflow, ignored source high bits, `rd == rt`, GPR zero,
reserved `rs`, PC wrap, and exact events. Twelve boundary plus 512 sequential
randomized cases make DSLL the twenty-third complete ISA coverage entry.

Canonical DSRL is the matching logical-right low-range doubleword shift.
SPECIAL function `0x3a` requires reserved `rs` to be zero, reads only
`rt[63:0]`, and zero-fills from the left for encoded counts 0 through 31. It
preserves old destination bits 127:64 and never sign-extends source bit 63.
Directed checks cover counts 0, 1, 30, and 31, zero fill, ignored source high
bits, `rd == rt`, GPR zero, reserved `rs`, PC wrap, and exact events. Twelve
boundary plus 512 sequential randomized cases make DSRL the twenty-fourth
complete ISA coverage entry.

Canonical DSRA completes the implemented low-range immediate doubleword shift
trio. SPECIAL function `0x3b` requires reserved `rs` to be zero, interprets
`rt[63:0]` as signed two's complement, and sign-fills from bit 63 for encoded
counts 0 through 31. Old destination bits 127:64 remain intact. Directed checks
cover both operand signs, counts 0, 1, 30, and 31, `rd == rt`, GPR zero,
reserved `rs`, PC wrap, and exact events. Twelve boundary plus 512 sequential
randomized cases make DSRA the twenty-fifth complete ISA coverage entry.

DSLL32 function `0x3c` widens the encoded count before shifting, implementing
effective counts 32 through 63 while preserving destination bits 127:64.
DSRL32 function `0x3e` uses the same widened count for logical-right shifts,
zero-fills the low doubleword, and preserves the destination upper lane.
Directed and 524-case randomized differential checks make it the twenty-seventh
complete ISA coverage entry.
DSRA32 function `0x3f` completes the high-range immediate doubleword trio. It
uses signed arithmetic right shift for effective counts 32 through 63, retaining
source sign fill only within the low doubleword and preserving destination bits
127:64. Positive, negative, alias, zero-register, exact-event, and 524-case
differential checks make it the twenty-eighth complete ISA coverage entry.
DSLLV function `0x14` begins variable doubleword shifts. Unlike word SLLV, its
count is `rs[5:0]`; values 32 through 63 therefore remain distinct instead of
wrapping modulo 32. It shifts only `rt[63:0]`, preserves the destination upper
lane, and is verified across every alias plus a 524-case sequential differential
stream, making it the twenty-ninth complete ISA coverage entry.
DSRLV function `0x16` applies the same six-bit count rules to a zero-filling
logical-right shift. Directed count, alias, legality, and exact-event coverage
plus a 524-case differential stream make it the thirtieth complete ISA entry.
DSRAV function `0x17` completes the variable doubleword trio with a signed
arithmetic-right shift. It fills from `rt[63]`, masks the count to `rs[5:0]`,
and preserves destination bits 127:64. Positive and negative count boundaries,
all aliases, encoding legality, exact events, and a 524-case differential
stream make it the thirty-first complete ISA entry.
DADDIU primary opcode `0x19` begins the nontrapping doubleword arithmetic
group. It sign-extends the 16-bit immediate, adds it to `rs[63:0]` modulo 64,
and preserves old `rt[127:64]`. Signed-immediate extrema, carry and wrap,
aliasing, zero-register suppression, exact events, and a 524-case differential
stream make it the thirty-second complete ISA entry.
DADDU SPECIAL function `0x2d` adds both source low doublewords modulo 64 and
preserves old destination bits 127:64. Carry and wrap boundaries, every source
and destination alias, identical and zero sources, reserved-field legality,
exact events, and a 524-case differential stream make it the thirty-third
complete ISA entry.
DSUBU SPECIAL function `0x2f` subtracts the second source low doubleword from
the first modulo 64 and preserves old destination bits 127:64. Borrow and wrap
boundaries, operand ordering, every alias, identical and zero sources,
reserved-field legality, exact events, and a 524-case differential stream make
it the thirty-fourth complete ISA entry.

MULT SPECIAL function `0x18` begins primary multiply/divide execution. It
multiplies signed source words into a 64-bit product, then independently
sign-extends the high product word into HI and the low product word into LO.
The R5900 optional nonzero `rd` receives LO in bits 63:0 while retaining old
bits 127:64; destination zero does not suppress HI/LO updates. Signed extrema,
independent half-extension boundaries, every relevant alias, primary/secondary
state isolation, reserved-field legality, exact events, and a 524-case
differential stream make it the thirty-fifth complete ISA entry.

MULTU SPECIAL function `0x19` uses the same primary destinations and optional
`rd` behavior while multiplying unsigned source words. The high and low product
words are nevertheless independently sign-extended into HI and LO. Unsigned
extrema, signed-versus-unsigned divergence, half-extension boundaries, every
relevant alias, primary/secondary state isolation, reserved-field legality,
exact events, and a 524-case differential stream make it the thirty-sixth
complete ISA entry.

DIV SPECIAL function `0x1a` divides the signed low source words, truncates the
quotient toward zero into primary LO, and places the correspondingly signed
remainder in primary HI. The overflow pair `0x80000000 / 0xffffffff` produces
zero remainder and sign-extended `0x80000000`; a zero divisor leaves the signed
dividend in HI and produces LO of one for a negative dividend or all ones
otherwise. DIV never writes a GPR or raises an arithmetic exception in this
functional model. All sign combinations, both edge classes, ignored upper
source lanes, source aliases, zero register, primary/secondary state isolation,
reserved-field legality, exact events, and a 524-case differential stream make
it the thirty-seventh complete ISA entry.

DIVU SPECIAL function `0x1b` divides unsigned low source words and independently
sign-extends the 32-bit remainder into primary HI and quotient into primary LO.
This extension remains signed even though the operands and arithmetic are
unsigned. A zero divisor produces all ones in LO and the sign-extended dividend
word in HI. DIVU never writes a GPR or raises an arithmetic exception in this
functional model. Unsigned extrema, quotient and remainder sign-bit boundaries,
signed-versus-unsigned divergence, five divisor-zero dividend classes, ignored
upper source lanes, source aliases, zero register, primary/secondary state
isolation, reserved-field legality, exact events, and a 524-case differential
stream make it the thirty-eighth complete ISA entry.

MFHI SPECIAL function `0x10` copies all 64 primary HI bits into the destination
GPR scalar lane and preserves old destination bits 127:64. Destination zero is
suppressed by the same centralized writeback boundary as other GPR-producing
operations, while HI, LO, HI1, and LO1 remain unchanged. Full-width HI boundary
classes, destination upper-lane preservation, destination zero, PC wrap, every
reserved field, exact events, and a 520-case differential stream varying both
HI and `rd` make it the thirty-ninth complete ISA entry. The functional model
does not claim the base manual's instruction-spacing hazard timing; that remains
part of the later pipeline-accuracy roadmap.

MFLO SPECIAL function `0x12` copies all 64 primary LO bits into the destination
GPR scalar lane and preserves old destination bits 127:64. Destination zero is
suppressed, while HI, LO, HI1, and LO1 remain unchanged. Full-width LO boundary
classes, destination upper-lane preservation, destination zero, PC wrap, every
reserved field, exact events, and a 520-case differential stream varying both
LO and `rd` make it the fortieth complete ISA entry. As with MFHI, functional
coverage does not claim the base manual's instruction-spacing hazard timing.

MTHI SPECIAL function `0x11` copies source GPR bits 63:0 into primary HI while
ignoring bits 127:64. It writes no GPR and leaves LO, HI1, and LO1 unchanged.
Full-width scalar boundaries under an asymmetric upper GPR lane, source zero,
PC wrap, every reserved field, exact events, and a 520-case differential stream
varying the complete 128-bit source and `rs` make it the forty-first complete
ISA entry. Functional coverage does not claim the base manual's HI/LO
instruction-spacing hazard timing.

MTLO SPECIAL function `0x13` copies source GPR bits 63:0 into primary LO while
ignoring bits 127:64. It writes no GPR and leaves HI, HI1, and LO1 unchanged.
Full-width scalar boundaries under an asymmetric upper GPR lane, source zero,
PC wrap, every reserved field, exact events, and a 520-case differential stream
varying the complete 128-bit source and `rs` make it the forty-second complete
ISA entry. Functional coverage does not claim the base manual's HI/LO
instruction-spacing hazard timing.

Canonical LUI is the first admitted primary-opcode instruction. Opcode `0x0f`
requires reserved `rs` to be zero. Its immediate occupies word bits 31:16 and
the resulting word is sign-extended through bits 63:32, while old `rt` bits
127:64 remain intact. Five boundary plus 512 randomized cases cover immediate
extrema, destination zero, reserved encoding, PC wrap, and exact events, making
LUI the eighth complete ISA coverage entry.

Canonical ORI admits every `rs`, `rt`, and 16-bit immediate under primary opcode
`0x0d`. It zero-extends the immediate and ORs it with source bits 63:0; old
destination bits 127:64 remain intact. Separate source and destination values,
both alias directions, source and destination zero, PC wrap, exact events, and
the five immediate boundary classes are directed checks. Eight boundary plus
512 randomized cases make ORI the ninth complete ISA coverage entry.

Canonical ANDI admits every `rs`, `rt`, and 16-bit immediate under primary
opcode `0x0c`. It ANDs source bits 63:0 with the zero-extended immediate, so
scalar bits 63:16 clear while old destination bits 127:64 remain intact.
Separate source and destination values, aliasing, source and destination zero,
PC wrap, exact events, and the five immediate boundary classes are directed
checks. Eight boundary plus 512 randomized cases make ANDI the tenth complete
ISA coverage entry.

Canonical XORI admits every `rs`, `rt`, and 16-bit immediate under primary
opcode `0x0e`. It XORs source bits 63:0 with the zero-extended immediate, while
old destination bits 127:64 remain intact. Separate source and destination
values, aliasing, source and destination zero, PC wrap, exact events, and the
five immediate boundary classes are directed checks. Eight boundary plus 512
randomized cases make XORI the eleventh complete ISA coverage entry and finish
the initial logical-immediate family.

Canonical ADDIU admits every `rs`, `rt`, and 16-bit immediate under primary
opcode `0x09`. It sign-extends the immediate, adds it to source bits 31:0 modulo
32 bits without an overflow exception, sign-extends the result through bits
63:32, and retains old destination bits 127:64. Directed checks cover immediate
extrema, positive and negative wrap, ignored source high bits, aliasing,
destination zero, PC wrap, and exact events. Twelve boundary plus 512 randomized
cases make ADDIU the twelfth complete ISA coverage entry.

Canonical ADDU admits every `rs`, `rt`, and `rd` under SPECIAL function `0x21`
when reserved `sa` is zero. It adds source bits 31:0 modulo 32 bits without an
overflow exception, sign-extends the result through bits 63:32, and retains old
destination bits 127:64. Directed checks cover signed extrema, carry wrap,
ignored source high bits, both destination aliases, identical sources, register
zero, PC wrap, exact events, and reserved-field rejection. Twelve boundary plus
512 randomized cases make ADDU the thirteenth complete ISA coverage entry.

Canonical SUBU admits every `rs`, `rt`, and `rd` under SPECIAL function `0x23`
when reserved `sa` is zero. It subtracts source bits 31:0 modulo 32 bits without
an overflow exception, sign-extends the result through bits 63:32, and retains
old destination bits 127:64. Directed checks cover signed extrema, borrow wrap,
operand order, ignored source high bits, both destination aliases, identical
sources, register zero, PC wrap, exact events, and reserved-field rejection.
Twelve boundary plus 512 randomized cases make SUBU the fourteenth complete ISA
coverage entry.

Canonical AND admits every `rs`, `rt`, and `rd` under SPECIAL function `0x24`
when reserved `sa` is zero. It combines both low 64-bit scalar source lanes and
retains old destination bits 127:64. Directed checks cover zero, all-ones,
alternating, sparse, cross-word, and bit-63 patterns; ignored source upper lanes;
both destination aliases; identical sources; register zero; PC wrap; exact
events; and reserved-field rejection. Twelve boundary plus 512 randomized cases
make AND the fifteenth complete ISA coverage entry.

Canonical OR admits every `rs`, `rt`, and `rd` under SPECIAL function `0x25`
when reserved `sa` is zero. It combines both low 64-bit scalar source lanes and
retains old destination bits 127:64. Directed checks cover zero, all-ones,
alternating, sparse, disjoint, cross-word, and bit-63 patterns; ignored source
upper lanes; both destination aliases; identical sources; register zero; PC
wrap; exact events; and reserved-field rejection. Twelve boundary plus 512
randomized cases make OR the sixteenth complete ISA coverage entry.

Canonical XOR admits every `rs`, `rt`, and `rd` under SPECIAL function `0x26`
when reserved `sa` is zero. It combines both low 64-bit scalar source lanes and
retains old destination bits 127:64. Directed checks cover zero, all-ones,
alternating, sparse, self-cancellation, cross-word, and bit-63 patterns; ignored
source upper lanes; both destination aliases; register zero; PC wrap; exact
events; and reserved-field rejection. Twelve boundary plus 512 randomized cases
make XOR the seventeenth complete ISA coverage entry.

Canonical NOR admits every `rs`, `rt`, and `rd` under SPECIAL function `0x27`
when reserved `sa` is zero. It complements the inclusive combination of both
low 64-bit scalar source lanes and retains old destination bits 127:64.
Directed checks cover zero, all-ones, alternating, sparse, cross-word, and
bit-63 patterns; the exact 64-bit complement boundary; ignored source upper
lanes; both destination aliases; identical sources; register zero; PC wrap;
exact events; and reserved-field rejection. Twelve boundary plus 512 randomized
cases make NOR the eighteenth complete ISA coverage entry.

Canonical SLT admits every `rs`, `rt`, and `rd` under SPECIAL function `0x2a`
when reserved `sa` is zero. It compares both low 64-bit scalar source lanes as
signed integers, writes exactly zero or one to the destination scalar lane, and
retains old destination bits 127:64. Directed checks cover equality, signed
minimum and maximum, sign boundaries, and values whose 32-bit and 64-bit
orderings conflict; ignored source upper lanes; both destination aliases;
register zero; PC wrap; exact events; and reserved-field rejection. Twelve
boundary plus 512 randomized cases make SLT the nineteenth complete ISA
coverage entry.

Canonical SLTU admits every `rs`, `rt`, and `rd` under SPECIAL function
`0x2b` when reserved `sa` is zero. It compares both low 64-bit scalar source
lanes as unsigned integers, writes exactly zero or one to the destination
scalar lane, and retains old destination bits 127:64. Directed checks cover
equality, zero, one, unsigned maximum, bits 31, 32, and 63, and cases where
signed and unsigned order differ; ignored source upper lanes; both destination
aliases; register zero; PC wrap; exact events; and reserved-field rejection.
Twelve boundary plus 512 randomized cases make SLTU the twentieth complete ISA
coverage entry.

Canonical SLTI admits every `rs`, `rt`, and 16-bit immediate under primary
opcode `0x0a`. It sign-extends the immediate through 64 bits, compares it with
the signed low 64-bit source scalar lane, writes exactly zero or one to the
destination scalar lane, and retains old destination bits 127:64. Directed
checks cover signed scalar and immediate extrema, equality, sign-extension
boundaries, and values whose 32-bit and 64-bit signs conflict; ignored source
upper lanes; source/destination aliasing; register zero; PC wrap; and exact
events. Twelve boundary plus 512 randomized cases make SLTI the twenty-first
complete ISA coverage entry.

Canonical SLTIU admits every `rs`, `rt`, and 16-bit immediate under primary
opcode `0x0b`. It sign-extends the immediate through 64 bits, compares the
resulting bit pattern with the unsigned low 64-bit source scalar lane, writes
exactly zero or one to the destination scalar lane, and retains old destination
bits 127:64. Directed checks cover positive and negative immediate boundaries,
equality at both sign-extended extrema, adjacent unsigned values, ignored
source upper lanes, source/destination aliasing, register zero, PC wrap, and
exact events. Twelve boundary plus 512 randomized cases make SLTIU the
twenty-second complete ISA coverage entry and finish the functional foundation
matrix.

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
directed, randomized-differential, and exception coverage separately. All 22
foundation entries and 20 extension entries are complete; they began pending
because an encoding string
and milestone owner are a plan, not an implementation claim. A validator
cross-checks exact inventory, roadmap ownership, reference provenance, and
summary-state consistency. Fetch-to-RAM integration, sequential NOP execution,
and a generated arithmetic EE ELF are now complete. The next planning milestone
expands the roadmap from the initial scalar foundation into 64-bit operations
and HI/LO-family behavior.

## Deferred behavior

The following are intentionally outside the first foundation roadmap:

- remaining 64-bit scalar operations and R5900-specific 128-bit extension
  details not established by completed instruction milestones;
- remaining multiply, divide, HI/LO-family operations, and known R5900 subset
  differences;
- jumps, branches, link behavior, branch-likely nullification, and delay slots;
- data loads and stores, alignment exceptions, and unaligned merge operations;
- architectural exceptions, COP0, interrupt entry, caches, and TLB behavior;
- COP1/FPU, COP2/VU0 macro mode, and MMI instructions;
- pipeline, dual-issue, hazard, and cycle accuracy.

Before each group begins, its documented functionality is enumerated into the
roadmap and coverage database using the same tested planning gate.
