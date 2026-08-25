# References and Provenance

This project is a clean reimplementation. Significant sources will be recorded
with URL, relevant subsystem, known license, whether source code was consulted,
and provenance notes before they guide implementation.

No BIOS, game image, proprietary SDK material, leaked source, confidential
documentation, key, or circumvention material may be downloaded or committed.

Primary technical references will be researched and recorded in milestone
M012.

## Verification tooling

### cocotb documentation and source distribution

- URL: <https://docs.cocotb.org/en/development/master-notes.html>
- Relevant subsystem: verification infrastructure
- License: BSD-3-Clause
- Source code consulted: no; an exact official source revision is installed as
  a development dependency because it adds host Python 3.14 support
- Provenance notes: dependency revision is pinned in `requirements-dev.txt`;
  fetched content remains outside Git in `.venv`

### Verilator installation and container documentation

- URL: <https://verilator.org/guide/latest/install.html>
- Relevant subsystem: build and continuous-integration infrastructure
- License: LGPL-3.0-or-later OR Artistic-2.0 for the Verilator implementation
- Source code consulted: no
- Provenance notes: CI uses the official release container pinned to `v5.050`

### GitHub setup-python documentation

- URL: <https://github.com/actions/setup-python>
- Relevant subsystem: continuous-integration infrastructure
- License: MIT
- Source code consulted: no
- Provenance notes: CI pins the v6 action commit and Python 3.14
