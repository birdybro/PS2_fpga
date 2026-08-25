# Simulation Platform

Phase 1 builds a deterministic execution environment around synthesizable
interfaces. It does not model RDRAM timing and does not yet execute a CPU.

## Implemented infrastructure

- M015 provides `sim_clock`, a simulation-only clock source with a 10 ns default
  period, low initial level, 1 ps precision, and a fatal parameter check for
  periods that cannot be divided into equal half cycles.

## Planned boundaries

- Synthesizable transaction and RAM logic lives under `rtl/memory/`.
- Clocking, reset sequencing, file loaders, termination control, and trace sinks
  are simulation-only and live under `sim/`.
- Loader parsing is independently unit-tested before it writes simulated RAM.
- The simulation top composes clock, reset, one memory transaction interface,
  behavioral RAM, termination control, trace controls, and waveform controls.
- External software inputs are explicit command-line paths. No BIOS or game
  image is built into the simulator or repository.

## Initial memory contract

The first bus is a single-request, single-response interface with explicit
request validity, write intent, byte address, transfer width, write data, and
byte enables. A request is accepted exactly once on ready/valid handshake. The
response is independently backpressured. Protocol assertions cover request
stability, supported transfer sizes, response stability, and no response without
an accepted request.

Behavioral system RAM is little-endian and byte-addressed. Byte lane zero maps
to the lowest address. The roadmap adds 32-, 64-, and 128-bit aligned accesses
one direction at a time, then response latency. Alignment errors and CPU-visible
exceptions are later architectural milestones; early RAM tests reject malformed
testbench transactions rather than inventing CPU behavior.

## Loader contract

The raw loader copies an explicit binary to a caller-selected byte address. The
ELF loader initially supports only the legal EE test format established by a
future toolchain milestone. Header identification, target validation, loadable
segments, zero-fill, and entry-point publication are separate steps. Bounds,
overlap, overflow, malformed-input, and endianness cases receive directed tests.

Downloaded or user-supplied programs remain external unless a tiny purpose-built
fixture is clearly licensed and intentionally reviewed for inclusion.

## Control and observability

Cycle timeout, PASS, and FAIL are distinct mechanisms with deterministic exit
status. Memory and architectural traces are optional and silent by default.
Waveform controls reuse the existing ignored build-output policy. Trace or debug
logic must not change architectural state.

## Phase 1 exit

Phase 1 exits with two integration tests: one places a raw binary into RAM and
reads it back through the transaction interface; the other parses an EE ELF,
loads its segments and zero-fill, and publishes the entry point. CPU execution
starts only after the Phase 2 foundation is expanded into instruction-sized
milestones.
