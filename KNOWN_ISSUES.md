# Known Issues

## Unimplemented architecture

The Phase 1 simulation platform, loaders, behavioral RAM, and debug controls are
implemented. Phase 2 now has isolated R5900 GPR, PC, control, and instruction
fetch request/response RTL, but these blocks are not yet composed into an
executing CPU. This is not a claim of CPU compatibility.

Instruction fetch request and response paths are independently implemented but
not yet composed with control or RAM. Bus errors are retained as functional
fetch status; architectural exception handling, instruction decode, and
execution remain unimplemented.

All 22 entries in the initial R5900 ISA coverage matrix are pending. The matrix
records planned encodings and ownership, not corroborated implementation
semantics; each row must pass its instruction milestone before becoming
complete.

No consulted public R5900 source defines the post-reset values of GPR 1 through
31. The physical storage therefore has no reset input and tests initialize every
location before reading it. The public R10000 reset rule is recorded only as a
caution against assuming generic MIPS GPR zeroing, not as R5900 behavior.

The standalone PC loads the simulation harness's selected ELF start address
while reset is asserted. This is not the physical EE reset vector, a COP0 reset
model, or BIOS boot behavior; those remain deferred and the port must not be
interpreted as an architectural reset claim.

Public base-MIPS documentation does not by itself establish R5900-specific
instruction inclusion, opcode differences, 128-bit GPR destination-extension
rules, COP0 behavior, or FPU behavior. Each implementation milestone must
resolve its own evidence boundary. Until then those behaviors remain
unimplemented rather than approximated.

## Accuracy annotations

Temporary approximations must be marked `TODO-ACCURACY` in code and described
here with a replacement milestone. There are no such approximations yet.
