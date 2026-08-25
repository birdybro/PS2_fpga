# Known Issues

## Unimplemented architecture

The Phase 1 simulation platform, loaders, behavioral RAM, and debug controls are
implemented, but no PS2 architectural execution RTL exists yet. The active
Phase 2 work begins with a tested R5900 roadmap and coverage baseline; this is
not a claim of CPU compatibility.

All 22 entries in the initial R5900 ISA coverage matrix are pending. The matrix
records planned encodings and ownership, not corroborated implementation
semantics; each row must pass its instruction milestone before becoming
complete.

Public base-MIPS documentation does not by itself establish R5900-specific
instruction inclusion, opcode differences, 128-bit GPR destination-extension
rules, COP0 behavior, or FPU behavior. Each implementation milestone must
resolve its own evidence boundary. Until then those behaviors remain
unimplemented rather than approximated.

## Accuracy annotations

Temporary approximations must be marked `TODO-ACCURACY` in code and described
here with a replacement milestone. There are no such approximations yet.
