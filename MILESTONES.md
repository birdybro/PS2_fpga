# Milestones

Each milestone is one narrow, independently verifiable behavior. A milestone
is complete only after its targeted checks, the complete regression, and lint
all pass; documentation and persistent state are updated; the diff is reviewed;
and the milestone is committed and pushed when remote access permits.

Allowed states are `pending`, `active`, `blocked`, and `complete`. The
machine-readable source of truth is [milestones.yaml](milestones.yaml).

Phase 0 establishes repository and verification infrastructure. Later phases
will be expanded into similarly granular milestones before implementation.

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
