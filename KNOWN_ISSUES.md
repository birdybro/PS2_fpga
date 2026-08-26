# Known Issues

## Unimplemented architecture

The Phase 1 simulation platform, loaders, behavioral RAM, and debug controls are
implemented. Phase 2 composes GPR, PC, control, fetch, decode, execute, and
writeback RTL into a functional single-issue core. A generated EE ELF executes
13 straight-line instructions and reaches deterministic PASS, but this is not
a claim of general CPU compatibility.

Bus errors are retained as functional fetch status. Exact zero-word NOP, all
six canonical 32-bit shifts, DSLL, DSRL, DSRA, DSLL32, DSRL32, DSRA32, DSLLV, DSRLV, DSRAV, LUI, ORI, ANDI, XORI, ADDIU, DADDIU, ADDU, DADDU, SUBU, DSUBU, MULT, MULTU, DIV, DIVU, MFHI, MFLO, MTHI, MTLO, MULT1, MULTU1,
AND, OR, XOR, NOR, SLT, SLTU, SLTI, and SLTIU execute with PC advance,
retirement trace, and centralized writeback. No other instruction executes. Illegal words emit a
functional diagnostic and are suppressed before execution, but do not enter an
architectural exception; COP0 remains unimplemented.

GPR writeback uses a functional one-commit-per-asserted-episode protocol. It is
not a model of EE retirement, dual issue, pipeline hazards, or precise exception
timing.

All 22 entries in the initial scalar foundation are complete. Twenty-two of the
32 rows added by the doubleword and dual-HI/LO roadmap are complete; the other 10
are pending and each must pass its own
instruction milestone before becoming complete.

The R5900-specific tables omit generic MIPS `DMULT`, `DMULTU`, `DDIV`, and
`DDIVU`, so they are intentionally absent instead of inherited from the base
manual. Trapping `DADDI`, `DADD`, and `DSUB` remain deferred until architectural
integer-overflow exception entry exists.

Public sources establish four 64-bit multiply/divide registers (`HI`, `LO`,
`HI1`, and `LO1`) but not their post-reset values. The standalone RTL storage
therefore has no reset or initialization construct, and tests seed every field
before observation. Primary HI/LO writes are connected to the functional core;
secondary HI1/LO1 writes are connected for MULT1 and MULTU1, while the remaining
pipeline-1 producers are pending.

MULT1 and MULTU1 optional-`rd` results are resolved. The corresponding R5900
optional-`rd` results for `MADD`, `MADDU`, and their pipeline-1 forms require
semantic and destination-width corroboration before M113 through M116 can
complete. R5900
signed-overflow and divide-by-zero results require the same treatment in M107
and M108. Until those milestones resolve them, these operations
remain unimplemented rather than approximated.

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
