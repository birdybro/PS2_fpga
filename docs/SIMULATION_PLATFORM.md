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
- M023 adds aligned 64-bit reads for size encoding three. Eight consecutive
  bytes are returned little-endian in response bits 63:0 with all upper bits
  zero; 32-bit transfers retain their existing behavior.
- M024 adds aligned 64-bit writes with every lower-eight-lane byte-enable
  pattern, including a zero-strobe no-op. Disabled bytes remain unchanged,
  upper strobe lanes are rejected, and narrower accesses remain supported.
- M025 adds aligned 128-bit reads for size encoding four. Sixteen consecutive
  bytes fill the response in little-endian byte-lane order while all previously
  implemented 32- and 64-bit transfers retain their behavior.
- M026 completes aligned 128-bit writes. Every one of the 16 byte-enable lanes
  independently controls its little-endian storage byte, including the valid
  zero-strobe no-op, while narrower transfers remain supported.
- M027 parameterizes inserted response wait cycles. The default zero preserves
  existing behavior; a positive value captures read data and applies writes at
  acceptance, blocks new requests while pending, and asserts the completion
  after exactly the configured number of rising edges. This is a verification
  control, not an RDRAM timing claim.

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

M028 provides an atomic raw loader for a caller-owned `bytearray`. It accepts an
explicit bytes-like image or file path, validates the complete half-open
destination range before mutation, preserves all surrounding bytes, and reports
the loaded start, size, and exclusive end. Empty data at the memory end is a
valid no-op. The file API reads only caller-selected external content; it does
not embed software or firmware in the simulator.

The ELF loader initially supports only the legal EE test format established by
a future toolchain milestone. Header identification, target validation,
loadable segments, zero-fill, and entry-point publication are separate steps.
Bounds, overlap, overflow, malformed-input, and endianness cases receive
directed tests.

M029 implements the first of those steps: generic ELF32 identification and the
fixed 52-byte `Elf32_Ehdr` are decoded into an immutable record. The parser
accepts either ABI-defined byte order, requires the ELF magic, ELF32 class,
valid data encoding, current identification/header versions, and the declared
ELF32 header size, and ignores reserved identification padding. It neither
accepts an EE target nor changes memory; those are later milestones.

M030 adds the deliberately narrow EE target policy above that generic parser.
An accepted test image must be an executable object (`ET_EXEC`), identify the
MIPS architecture (`EM_MIPS`, value 8), and declare little-endian data. The
validator does not restrict OS ABI, ABI version, or processor flags without a
documented requirement. This keeps generic ELF decoding distinct from target
admission and avoids inventing toolchain policy. Memory remains untouched.

M031 decodes the fixed 32-byte `Elf32_Phdr` table and atomically copies the
file-backed bytes of each `PT_LOAD` entry. System V defines `p_vaddr` as the
in-memory destination and reserves `p_paddr`; PS2SDK's licensed EE loader uses
the same virtual-address rule. Before any memory change, the simulator validates
the complete table and load plan: entry size, table/source/destination bounds,
ELF32 range overflow, `p_filesz <= p_memsz`, alignment and congruence, ascending
virtual addresses, and non-overlapping full memory ranges. Non-load entries are
ignored. Only `p_filesz` bytes are copied in this milestone; the remainder up to
`p_memsz` is deliberately preserved by the file-only diagnostic API.

M032 adds the complete segment-loading API. It reuses the same whole-image plan,
copies each file payload, and then writes zero to exactly the half-open tail
`[p_vaddr + p_filesz, p_vaddr + p_memsz)`. Segments with equal file and memory
sizes leave adjacent RAM untouched; segments with no file bytes may initialize
an entire BSS range. Validation still completes before the first copy or clear,
so a malformed later segment cannot partially alter an earlier one.

M033 adds an immutable complete-image result containing the exact 32-bit
`e_entry` value and the tuple of loaded segments. Entry publication occurs only
after target, table, and segment validation and complete data/BSS initialization.
The loader does not require the entry point to fall inside a load segment: ELF
defines zero for an image with no associated entry, and later CPU or executable
policy may impose narrower start-address requirements with separate evidence.

Downloaded or user-supplied programs remain external unless a tiny purpose-built
fixture is clearly licensed and intentionally reviewed for inclusion.

## Control and observability

Cycle timeout, PASS, and FAIL are distinct mechanisms with deterministic exit
status. Memory and architectural traces are optional and silent by default.
Waveform controls reuse the existing ignored build-output policy. Trace or debug
logic must not change architectural state.

M034 provides the simulation-only cycle watchdog. `MAX_CYCLES=0` disables it;
otherwise the first rising edge with reset deasserted is active cycle 1 and the
watchdog times out exactly on active cycle N. Timeout status and the saturated
32-bit count remain sticky until synchronous active-low reset. The platform
configuration is fatal by default with a stable `SIM_TIMEOUT` diagnostic. A
separate fatal-suppression parameter exists only so isolated verification can
observe the boundary outputs; it is not an architectural control.

M035 adds reset-aware PASS termination. The first sampled PASS request in a
reset epoch emits a one-cycle event, latches completed status, prints exactly
one `SIM_PASS` marker, and calls `$finish` by default for successful simulator
exit. Held or repeated requests cannot retrigger until synchronous reset clears
the state. Isolated cocotb verification suppresses `$finish` to observe those
outputs because cocotb correctly classifies an HDL shutdown during an active
test as premature; the real default completion path is therefore also exercised
as a standalone Verilator binary and must return status zero.

M036 adds coded FAIL termination to the same one-result-per-reset state. The
first FAIL captures its complete 32-bit code, emits one event, latches failure,
prints `SIM_FAIL` with that code, and calls `$fatal` by default for nonzero exit.
A prior PASS or FAIL makes every later request inert. If PASS and FAIL arrive on
the same edge, FAIL has explicit priority and no PASS marker or state is emitted.
Synchronous reset clears both result classes and the captured code. This keeps
software failure distinct from watchdog `SIM_TIMEOUT` and infrastructure errors.

M037 adds a passive memory transaction trace sink. Its compile-time default is
disabled and opens no file. When enabled, `+MEM_TRACE_FILE=<path>` selects an
external ignored output (with a local fallback name), and the sink writes one
versioned header followed only by accepted ready/valid handshakes. Active cycles
start at 1 after reset. Request records contain write, 32-bit address, size,
128-bit write data, and 16 strobes; response records contain 128-bit read data
and error. Stalls and reset-time signals are silent. If request and response
complete together, the request record is written first. The monitor observes but
never drives the transaction interface or architectural state.

M038 adds a passive architectural event trace sink. It is disabled by default
and therefore creates no file; an enabled instance accepts
`+ARCH_TRACE_FILE=<path>` and otherwise uses `architectural_trace.log`. Each
asserted `event_valid_i` outside reset produces one record containing active
cycle, zero-based event sequence, 8-bit source and kind tags, 32-bit PC and
instruction, a 16-bit identifier, and a 128-bit value. The source and kind tags
are transport fields whose meaning belongs to the future subsystem adapter, so
this milestone does not invent CPU retirement, exception, or register-number
semantics. Inactive cycles and reset-time inputs are silent; reset restarts both
the active-cycle and event-sequence counters. The sink has no ready signal and
cannot stall or modify its producer.

M039 adds `sim_waveform_control`, a simulation-only VCD controller for the
future composed platform. `WAVE_ENABLE=0` is the default and performs no dump
system tasks, even when the simulator binary was compiled with trace support.
An enabled instance takes its output from `+WAVE_FILE=<path>`, with `waves.vcd`
as a fallback, and starts a whole-design `$dumpvars` capture. `make waves`
exercises both settings and retains the enabled result under ignored `build/`;
ordinary verification removes its temporary enabled self-test capture. Trace
instrumentation remains a build concern, so enabling the RTL parameter still
requires Verilator's `--trace` option.

M040 assembles those controls as `ps2_sim_top`. The module owns clock and reset,
one 32-bit-address/128-bit-data `memory_bus_if`, behavioral RAM, protocol
checking, timeout, PASS/FAIL termination, both trace sinks, and waveform
control. Its parameters preserve the established defaults while exposing clock
period, reset length, RAM capacity and artificial response latency, timeout and
terminal behavior, and each observability enable independently. The temporary
external memory-master, RAM byte-backdoor, terminal request, and architectural
event ports are simulation harness boundaries. They allow incremental loaders
and CPU-independent verification; they do not claim to be console pins or
synthesizable architecture. Reset fans out to every stateful component, and RAM
request readiness remains low until the reset sequencer releases on a falling
edge.

M041 connects the existing raw-file loader to that platform in verification.
The test builds a sentinel-filled host memory image, loads a temporary external
raw file into one interior half-open range, initializes RTL RAM to the same
sentinel, and overlays only the loader-selected bytes through the backdoor.
Normal 32-, 64-, and 128-bit memory transactions then read payload, adjacent,
and upper-bound windows byte-for-byte. This proves the current simulation load
path without adding a hardware-visible loader port or committing a binary
fixture. The backdoor remains inactive during every transaction read.

M042 completes the Phase 1 integration boundary with a generated external EE
ELF. Two `PT_LOAD` records place file bytes at their virtual addresses, zero
their separate memory-only tails, preserve sentinel-filled gaps, and publish an
entry point inside the first segment. Verification overlays only the loader's
returned memory ranges through the RAM backdoor, then checks the entry, file,
BSS, adjacency, gap, and final RAM-boundary windows using normal transactions.
The fixture exists only in ignored `build/inputs/`; no executable or firmware is
committed. This establishes image placement and start-address publication, not
instruction execution.

M079 adds the first CPU-side owner of the composed platform memory bus.
`R5900_FETCH_ENABLE=1` selects the synthesizable R5900 fetch path in place of
the temporary external request driver; the default remains external so the
existing raw and ELF loader tests retain their narrow transaction harness.
The fetch-enabled integration test keeps an external write request asserted to
prove it is ignored, loads two words through the RAM backdoor, and observes
ordinary checked read transactions with a configured two-cycle response.
Reset behavior, little-endian data, one-outstanding accounting, response
latency, output buffering, downstream backpressure, and a second fetch are all
verified without adding a hardware-visible loader mechanism.

## Phase 1 exit

Phase 1 exits with two green integration tests: one places a raw binary into RAM
and reads it back through the transaction interface; the other parses an EE ELF,
loads its segments and zero-fill, and publishes the entry point. CPU execution
starts only after the Phase 2 foundation is expanded into instruction-sized
milestones.
