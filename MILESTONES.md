# Milestones

Each milestone is one narrow, independently verifiable behavior. A milestone
is complete only after its targeted checks, the complete regression, and lint
all pass; documentation and persistent state are updated; the diff is reviewed;
and the milestone is committed and pushed when remote access permits.

Allowed states are `pending`, `active`, `blocked`, and `complete`. The
machine-readable source of truth is [milestones.yaml](milestones.yaml).

Phase 0 establishes repository and verification infrastructure. Later phases
will be expanded into similarly granular milestones before implementation.
