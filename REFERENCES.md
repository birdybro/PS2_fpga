# References and Provenance

`references.yaml` is the authoritative machine-readable source catalog. Every
source records its URL, role, relevant subsystems, known license, whether source
code was consulted, redistribution treatment, consulted sections, and
provenance notes. This document explains how those records may be used.

## Clean reimplementation policy

Architectural decisions should prefer public first-party publications, public
standards, and independently authored hardware research. A single secondary
source is not enough evidence for uncertain or unusual behavior; such behavior
must be corroborated, isolated by a test, or recorded in `KNOWN_ISSUES.md` with
a `TODO-ACCURACY` marker.

The project does not download, inspect, or redistribute BIOS images, game
images, proprietary SDK material, leaked source, confidential documentation,
cryptographic keys, or circumvention material. Public mirrors describing their
contents as confidential are excluded even when readily accessible. A future
user-supplied BIOS must remain external to the repository.

Documents without clear redistribution permission remain link-only. Any useful
local download must live in an ignored cache and be reproducibly fetched; it
must never be committed merely because it is publicly reachable. Emulator
implementation source requires an explicit license and provenance review before
consultation. No emulator source has guided this implementation so far.

## Architecture and hardware

<!-- ref:sony-ee-announcement -->
### Sony Computer Entertainment Emotion Engine announcement

Official public overview of the Emotion Engine and published system
specifications. It establishes context, not detailed instruction behavior.

<!-- ref:toshiba-ee-announcement -->
### Toshiba Emotion Engine announcement

Official public Toshiba announcement used as an independent first-party check
of the joint design and high-level specifications.

<!-- ref:date2001-ee-cpu -->
### CPU for PlayStation 2

Public DATE 2001 paper authored by Sony Computer Entertainment and Toshiba
engineers. It covers the EE system architecture, CPU core, vector units,
on-chip interfaces, and the original design verification strategy.

<!-- ref:toshiba-2000-highlights -->
### Toshiba Review 2000 technical highlights

Official Toshiba technical overview used to corroborate the major EE block
relationships. The PDF is linked rather than copied.

<!-- ref:ps2tek -->
### PS2Tek

Independently authored PS2 hardware documentation with broad EE, DMAC, GIF,
VIF, VU, GS, IOP, and SIF coverage. The upstream repository does not state a
license, so it is link-only and architectural details require corroboration.

<!-- ref:sgi-mips-iv-index -->
### SGI MIPS IV Instruction Set archive index

Public archive index for the base MIPS IV instruction-set manual. It is useful
for base semantics only; R5900-specific deviations require PS2-specific
evidence.

## Homebrew software and toolchain

<!-- ref:ps2sdk -->
### PS2SDK

The public PS2 homebrew SDK is licensed under the Academic Free License 2.0.
Its README, API documentation, license, and sample makefile EE toolchain prefix
are approved inputs for software, loader, and register-interface planning. The
consulted `mips64r5900el-ps2-elf-` prefix corroborates the little-endian native
EE target. Its EE ELF loader's `PT_LOAD` destination behavior informed the
simulation-only M031 loader; no PS2SDK implementation source has guided
synthesizable RTL.

<!-- ref:binutils-r5900-review -->
### GNU Binutils R5900 support review

Public GNU maintainer discussion of accepted R5900 target support, including
the ISA subset, FPU limitations, MMI support, and ELF targets. Linked patch
source has not been copied or used as RTL implementation source.

<!-- ref:system-v-gabi-elf -->
### System V generic ABI ELF object file format

The public Xinuos generic ABI specification defines `e_ident`, ELF class and
data-encoding tags, `Elf32_Ehdr` and `Elf32_Phdr` layouts, and `PT_LOAD`
semantics. It guides generic container parsing in M029 and M031; PS2 EE target
acceptance remains the separate M030 policy using PS2/MIPS-specific evidence.

## Verification tooling

<!-- ref:cocotb-development-docs -->
### Cocotb development documentation

The official development documentation records Python 3.14 support. The exact
compatible revision is pinned in `requirements-dev.txt` and installed only in
the ignored `.venv`.

<!-- ref:verilator-install-docs -->
### Verilator installation and container documentation

Official documentation for the release containers used to pin CI to Verilator
5.050.

<!-- ref:setup-python-docs -->
### GitHub setup-python documentation

Official documentation for the commit-pinned CI action and Python version
selection.

## Updating the catalog

Before a source guides implementation, add it to `references.yaml` and add its
matching reference marker entry here. Record source-code consultation as
`true` only when implementation source was actually inspected for the relevant
behavior. Changes must pass `scripts/check_references.py`, unit tests, strict
lint, and the full regression.
