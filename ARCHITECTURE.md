# Architecture

PS2_fpga will separate synthesizable SystemVerilog under `rtl/` from
simulation-only models, loaders, and debug facilities under `sim/`. Reference
models will live under `reference/`, and verification will be divided into
unit, differential, randomized, integration, regression, and system tests.

The first implementation target is a deliberately simple multi-cycle R5900
execution core connected to behavioral memory. Pipeline and timing accuracy
are later, explicitly tracked work. `docs/R5900_FOUNDATION.md` defines the
initial state, control, evidence, verification, and deferral boundaries. The
timing-free immutable reference state in `reference/ee/r5900.py` contains the
128-bit GPRs, 32-bit PC, and independent 64-bit `HI`, `LO`, `HI1`, and `LO1`
registers. Its defaults are deterministic simulation setup, not a hardware
reset claim.
`rtl/ee/r5900/r5900_types_pkg.sv` defines the corresponding synthesizable
widths and packed observation records without implementing state storage.
`rtl/ee/r5900/r5900_gpr_storage.sv` is the reset-free physical two-read,
one-write array. `rtl/ee/r5900/r5900_gpr_file.sv` layers architectural
write suppression, read forcing, debug masking, and an invariant assertion for
all 128 bits of GPR zero above that storage.
`rtl/ee/r5900/r5900_hilo_state.sv` holds independent 64-bit `HI`, `LO`, `HI1`,
and `LO1` values behind four synchronous write enables. The functional core
connects primary HI/LO writes from execute; the secondary path remains
isolated until its instruction milestones. The block has no reset input;
verification explicitly seeds every field before observation because public
sources do not establish hardware reset contents.
`rtl/ee/r5900/r5900_pc.sv` holds the functional 32-bit PC and accepts an
external simulation start address; physical reset-vector policy remains outside
this early CPU boundary.
`rtl/ee/r5900/r5900_control.sv` is a five-state, completion-gated functional
sequencer. It expresses no pipeline, latency, issue-width, or hazard timing.
`rtl/ee/r5900/r5900_fetch_request.sv` converts an aligned PC into one latched
32-bit read request. It holds every request field through backpressure and
emits one acceptance event; response consumption remains a separate boundary.
The shared memory interface exposes request-initiator and response-consumer
modports so those paths can be verified independently before composition.
`rtl/ee/r5900/r5900_fetch_response.sv` arms from that request acceptance,
buffers the low 32 response bits plus error status, and retains them through
downstream backpressure. The one-entry receiver permits a same-cycle response
but rejects unsolicited responses and overlapping fetches.
`rtl/ee/r5900/r5900_fetch_path.sv` composes the request and response halves
into one synthesizable, single-fetch path. A registered request-acceptance
handoff prevents target readiness from feeding combinationally back through
response readiness, while start readiness excludes every pending request,
accepted request, expected response, or unconsumed instruction.
`rtl/ee/r5900/r5900_core.sv` is the first complete functional composition of
the PC, five-state controller, fetch path, decode/dispatch, scalar execute,
central writeback, and GPR file. It captures the fetched word before decode,
latches execute results before the writeback state, advances PC only after
completed execution, and emits retirement only from writeback. Its `run_i`
input gates only the start of a new fetch, allowing the simulation loader to
initialize RAM before execution; an eventual hardware top can tie it active.
`rtl/ee/r5900/r5900_instruction_fields.sv` is a timing-free combinational view
of the 32-bit instruction word. It exposes the overlapping MIPS opcode,
register, shift, function, immediate, and target fields plus explicit 32-bit
sign- and zero-extended immediates; it does not decide encoding legality.
`rtl/ee/r5900/r5900_decode.sv` is the explicit admission boundary. Its six-bit
operation enum admits exact word zero as NOP; canonical SPECIAL SLL, SRL, SRA,
SLLV, SRLV, SRAV, DSLLV, DSRLV, DSRAV, DSLL, DSRL, DSRA, DSLL32, DSRL32, DSRA32, ADDU, DADDU, SUBU, DSUBU, MULT, AND, OR, XOR, NOR,
SLT, and SLTU; and primary-opcode LUI, ORI, ANDI, XORI, ADDIU, DADDIU, SLTI, and SLTIU
encodings. Immediate shifts and LUI require reserved `rs` to be clear; variable
shifts and register ALU operations require reserved `sa` to be clear. Every unsupported word maps to no
operation with legality deasserted.
`rtl/ee/r5900/r5900_decode_dispatch.sv` gates valid decoded operations toward
execution. Unsupported words cannot dispatch and instead produce the packed
diagnostic record already defined by the R5900 type package, preserving their
exact PC and instruction. This is intentionally not COP0 exception entry.
`rtl/ee/r5900/r5900_writeback.sv` is the single architectural GPR commit
adapter. It accepts one commit per asserted episode, suppresses destination
zero, emits the same typed event used by debug and differential observation,
and drives the existing GPR file's index/value write port.
`rtl/ee/r5900/r5900_execute.sv` is the growing functional operation boundary.
NOP completes without writeback. SLL, SRL, SRA, SLLV, SRLV, and SRAV shift the
low source word left, logically right, arithmetically right, or left/right by
`rs[4:0]`, then sign-extend the 32-bit result through the low 64-bit scalar lane.
The shifts preserve the old destination's upper 64-bit lane and commit the
complete 128-bit value through centralized writeback. Every admitted operation
advances PC by four and emits a typed retirement record with the pre-advance PC
and exact instruction. DSLL, DSRL, and DSRA shift the complete low 64-bit source
lane left, logically right, or arithmetically right by the immediate count and
preserve destination bits 127:64. DSLL32 applies the same low-doubleword and
upper-lane rules as DSLL with an effective shift count of encoded `sa + 32`;
DSRL32 applies the corresponding zero-filling logical-right shift, while
DSRA32 sign-fills its widened arithmetic-right result from source bit 63.
DSLLV, DSRLV, and DSRAV shift the complete low doubleword left, logically
right, or arithmetically right by `rs[5:0]`, preserving counts 32 through 63
and destination bits 127:64. DSRAV takes its arithmetic fill from source bit
63.
LUI places its immediate in word bits 31:16, applies the
same scalar sign extension, and preserves the destination's upper 64 bits. The
ORI, ANDI, and XORI zero-extend their immediates, combine them with source bits
63:0, and also preserve the destination's upper 64 bits. ADDIU sign-extends its
immediate, adds modulo 32 bits without an overflow exception, and sign-extends
the word result through the scalar lane. DADDIU instead adds the sign-extended
immediate to all 64 source scalar bits modulo 64, preserves destination bits
127:64, and also cannot raise integer overflow. ADDU applies the same wrapping and
extension rules to the low words of two GPR sources. DADDU instead adds both
complete low 64-bit scalar lanes modulo 64 and preserves the old destination
upper lane; SUBU applies word rules to nontrapping modulo-32-bit subtraction,
while DSUBU subtracts complete low scalar lanes modulo 64 and preserves the
destination upper lane. MULT multiplies the signed low words, independently
sign-extends the product's high and low words into primary HI and LO, and
optionally writes LO to nonzero `rd` while preserving `rd[127:64]`. AND
combines the full low 64-bit scalar
lanes and preserves the old destination's upper lane; OR uses the same lane
rules for inclusive combination, XOR uses exclusive combination, and NOR
complements the 64-bit inclusive result without extending that complement into
the preserved upper lane. SLT compares both scalar lanes as signed 64-bit
values and replaces the destination scalar lane with exactly zero or one while
preserving its upper lane; SLTU applies the same result rules to an unsigned
64-bit comparison. SLTI sign-extends its 16-bit immediate to 64 bits, compares
it against the signed source scalar lane, and preserves the destination upper
lane around the Boolean result. SLTIU uses the same sign-extended immediate bit
pattern for an unsigned scalar comparison. The debug interface carries each
retirement record.

## Repository boundaries

- `rtl/` contains synthesis-oriented hardware organized by PS2 subsystem.
- `sim/` contains non-synthesizable models, loaders, debug, and the simulation top.
- `reference/` contains correctness-oriented models independent from the RTL.
- `coverage/` contains machine-readable architectural feature and verification state.
- `tests/` separates unit, differential, randomized, integration, regression,
  and system verification.
- `software/` contains source for legal, purpose-built bare-metal workloads.
- `scripts/` contains reproducible development and validation entry points.
- `docs/` contains detailed subsystem documentation as it is developed.
- `.github/workflows/` contains continuous-integration definitions.

## Simulation composition boundary

`sim/ps2_sim_top.sv` is the first composed simulation platform. It owns the
simulation clock and reset, behavioral RAM, the single-outstanding memory
protocol checker, timeout and PASS/FAIL controls, memory and architectural trace
sinks, and waveform control. Its temporary external memory-master and
architectural-event ports let loaders and verification drive the platform
before an EE core exists. With `R5900_FETCH_ENABLE`, the internal fetch path
owns that same memory interface instead, and the external memory-master inputs
are ignored. This parameterized selection preserves CPU-independent loader
tests while proving real instruction reads against the existing RAM and
protocol checker. Those ports are simulation harness boundaries, not PS2
architectural pins; later CPU integration will connect control and execution
without changing the RAM contract.

`R5900_CORE_ENABLE` selects the composed multi-cycle core as a third,
mutually-exclusive owner. The simulation-only EE run/start controls and packed
state/event outputs support deterministic program loading and observation; they
are not console pins. The first core image test executes four sequential NOPs
and then removes run permission before the next fetch.

In core mode, retirement automatically owns the architectural trace input with
source `0x01` (EE) and kind `0x01` (retirement); testbench-supplied trace events
are ignored. PC and instruction carry the exact retirement record, while the
identifier and value fields remain zero until a later milestone defines a
richer event adapter. This keeps trace capture passive and deterministic.

The RAM byte backdoor is likewise exposed only for loaders and verification.
It cannot appear on the eventual synthesizable `rtl/ps2_top.sv` boundary.

## Accuracy status

- Functional accuracy: the 22-instruction straight-line scalar foundation runs
  from loaded RAM through the composed multi-cycle core.
- Architectural accuracy: verified for the implemented scalar results, PC,
  GPR zero, entry point, retirement, writeback behavior, primary MULT updates,
  and isolated dual-HI/LO state storage.
- Timing accuracy: not yet implemented.
- FPGA readiness: not yet assessed.
