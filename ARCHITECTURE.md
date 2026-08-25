# Architecture

PS2_fpga will separate synthesizable SystemVerilog under `rtl/` from
simulation-only models, loaders, and debug facilities under `sim/`. Reference
models will live under `reference/`, and verification will be divided into
unit, differential, randomized, integration, regression, and system tests.

The first implementation target is a deliberately simple multi-cycle R5900
execution core connected to behavioral memory. Pipeline and timing accuracy
are later, explicitly tracked work. `docs/R5900_FOUNDATION.md` defines the
initial state, control, evidence, verification, and deferral boundaries. The
timing-free immutable reference state begins in `reference/ee/r5900.py`.
`rtl/ee/r5900/r5900_types_pkg.sv` defines the corresponding synthesizable
widths and packed observation records without implementing state storage.
`rtl/ee/r5900/r5900_gpr_storage.sv` is the reset-free physical two-read,
one-write array. `rtl/ee/r5900/r5900_gpr_file.sv` layers architectural
write suppression, read forcing, debug masking, and an invariant assertion for
all 128 bits of GPR zero above that storage.
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
`rtl/ee/r5900/r5900_instruction_fields.sv` is a timing-free combinational view
of the 32-bit instruction word. It exposes the overlapping MIPS opcode,
register, shift, function, immediate, and target fields plus explicit 32-bit
sign- and zero-extended immediates; it does not decide encoding legality.
`rtl/ee/r5900/r5900_decode.sv` is the explicit admission boundary. Its five-bit
operation enum admits exact word zero as NOP; canonical SPECIAL SLL, SRL, SRA,
SLLV, SRLV, and SRAV; and primary-opcode LUI, ORI, and ANDI encodings. Immediate
shifts and LUI require reserved `rs` to be clear; variable shifts require
reserved `sa` to be clear. Every unsupported word maps to no operation with
legality deasserted.
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
and exact instruction. LUI places its immediate in word bits 31:16, applies the
same scalar sign extension, and preserves the destination's upper 64 bits. The
ORI and ANDI zero-extend their immediates, combine them with source bits 63:0,
and also preserve the destination's upper 64 bits. The debug interface carries
each retirement record.

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
before an EE core exists. Those ports are simulation harness boundaries, not
PS2 architectural pins; later CPU integration will connect the same internal
memory transaction interface without changing the RAM contract.

The RAM byte backdoor is likewise exposed only for loaders and verification.
It cannot appear on the eventual synthesizable `rtl/ps2_top.sv` boundary.

## Accuracy status

- Functional accuracy: not yet implemented.
- Architectural accuracy: not yet implemented.
- Timing accuracy: not yet implemented.
- FPGA readiness: not yet assessed.
