# Simulation Platform

Phase 1 builds a deterministic execution environment around synthesizable
interfaces. It does not model RDRAM timing and does not yet execute a CPU.

## Implemented infrastructure

- M015 provides `sim_clock`, a simulation-only clock source with a 10 ns default
  period, low initial level, 1 ps precision, and a fatal parameter check for
  periods that cannot be divided into equal half cycles.
- M016 provides `sim_reset`, a simulation-only active-low reset sequencer. It
  asserts before the first clock edge, holds for four rising edges by default,
  releases on the following falling edge to avoid a sequential sampling race,
  and remains released thereafter.
- M017 provides the parameterized `memory_bus_if` ready/valid interface. Its
  default configuration carries 32-bit byte addresses and 128-bit payloads.
- M018 provides `memory_bus_protocol_checker`. It asserts valid size encodings,
  stable stalled payloads and valid signals, response causality, and at most one
  outstanding request while allowing zero-latency and same-cycle replacement.
- M019 provides `behavioral_system_ram`, a simulation-only byte array with
  explicit bounds reporting and a byte backdoor reserved for loaders and tests.
  Stored bytes survive reset; writes are suppressed while reset is asserted.
  Power-up byte contents are unspecified until a loader or test initializes them.
- M020 adds registered, aligned 32-bit reads through `memory_bus_if`. Read data
  is little-endian in bits 31:0 with upper response bits zero. Responses remain
  stable under backpressure; writes, other sizes, misalignment, and out-of-range
  requests are not accepted.
- M021 adds aligned full-word 32-bit writes when `req_wstrb` is exactly
  `16'h000f`. The low four write-data lanes update little-endian storage and the
  registered completion response carries zero data. Partial strobes remain
  unaccepted for M022.
- M022 accepts every lower-four-lane byte-enable pattern for aligned 32-bit
  writes, including a zero-strobe no-op. Disabled bytes remain unchanged and
  any strobe above lane three keeps the request unaccepted.

## Planned boundaries

- Synthesizable transaction definitions and protocol checking live under
  `rtl/memory/`.
- The initial simulation-first RAM lives under `sim/models/`; a future
  synthesizable replacement will preserve the architectural transaction
  boundary rather than expose its loader backdoor.
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

| Signal | Driven by | Default width | Meaning |
| --- | --- | ---: | --- |
| `req_valid` | initiator | 1 | Request payload is valid. |
| `req_ready` | target | 1 | Target can accept the request this cycle. |
| `req_write` | initiator | 1 | One for write, zero for read. |
| `req_addr` | initiator | 32 | Byte address of the transfer. |
| `req_size` | initiator | 3 | Log2 bytes: 0, 1, 2, 3, or 4 for 1 through 16 bytes. |
| `req_wdata` | initiator | 128 | Write payload; byte lane zero is bits 7:0. |
| `req_wstrb` | initiator | 16 | One bit per write-data byte lane. |
| `rsp_valid` | target | 1 | Response payload is valid. |
| `rsp_ready` | initiator | 1 | Initiator can accept the response this cycle. |
| `rsp_rdata` | target | 128 | Read payload in the same byte-lane order. |
| `rsp_error` | target | 1 | The accepted transfer failed. |

Request payload remains stable from assertion of `req_valid` through the cycle
where `req_ready` is also asserted. Response payload follows the equivalent
rule. Only one request may be outstanding, and every response follows one
accepted request. Zero-latency response is permitted. Read strobes and write
response data are ignored. M018 enforces these rules with fatal simulation
assertions and exposes outstanding state for verification and debug.

Behavioral system RAM is little-endian and byte-addressed. Byte lane zero maps
to the lowest address. The roadmap adds 32-, 64-, and 128-bit aligned accesses
one direction at a time, then response latency. Alignment errors and CPU-visible
exceptions are later architectural milestones; early RAM tests reject malformed
testbench transactions rather than inventing CPU behavior.

The simulation-only byte backdoor reports whether its address is in range,
returns zero for an out-of-range read, and ignores an out-of-range write. It is
not an architectural port and will not appear on `ps2_top`.

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
