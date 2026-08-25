# Milestones

Each milestone is one narrow, independently verifiable behavior. A milestone
is complete only after its targeted checks, the complete regression, and lint
all pass; documentation and persistent state are updated; the diff is reviewed;
and the milestone is committed and pushed when remote access permits.

Allowed states are `pending`, `active`, `blocked`, and `complete`. The
machine-readable source of truth is [milestones.yaml](milestones.yaml).

Phase 0 establishes repository and verification infrastructure. Phase 1 is
expanded into 28 implementation milestones covering clock/reset, the memory
transaction contract, each RAM width and direction, loaders, simulator control,
observability, top-level composition, and two integration gates. Phase 2 has a
dedicated roadmap-expansion boundary before R5900 implementation begins. The
first Phase 2 expansion adds 39 independently gated milestones covering the ISA
coverage database, reference and RTL state, fetch/decode/writeback foundations,
22 individual scalar encodings, and three CPU/platform execution gates.

The design contract and exit criteria for Phase 1 are documented in
`docs/SIMULATION_PLATFORM.md`; the first CPU boundary is documented in
`docs/R5900_FOUNDATION.md`. `scripts/check_roadmap.py` makes each enumerated
order, title, subsystem ownership, and one-step dependency a tested contract.
Later major subsystems will be expanded the same way before implementation.

## Machine-readable schema

Every entry requires `id`, `title`, `subsystem`, `status`, `dependencies`,
`tests`, `references`, `commit`, and `notes`. IDs use `M` plus three digits and
an optional uppercase subdivision suffix. Dependencies must name earlier
entries. Active and complete entries require all dependencies to be complete.

Exactly one entry is active during development. Complete entries require a Git
commit; the latest completion may use a temporary `self (...)` reference until
the following milestone records its exact hash. Non-complete entries use a null
commit. `scripts/check_milestones.py` enforces these rules and cross-checks the
resume fields in `PROGRESS.md`.
