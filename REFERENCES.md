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
