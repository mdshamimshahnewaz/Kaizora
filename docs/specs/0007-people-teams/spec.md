# 0007 — People & Teams

> Implementation update (2026-10-18): the owner authorized 0005–0008 in App UI and Django Admin. [Delivery decisions and evidence](../0005-0008-delivery.md) supersede the original draft-only labels below. Owner UI/UX acceptance is still pending.

Status: Implemented — owner UI/UX acceptance pending.
Date: 2026-10-18 · Constitution: 1.1 · Implementation authorised: Yes, by the owner on 2026-10-18.
Original planning detail is retained below; the delivery record documents adopted decisions, actual contracts and verification limits.

## Problem and scope
Maintain stable organization-owned resource profiles and team membership independently from user login access, so historical work remains attributable when people leave or accounts change.

## User stories
- US-1 (P0): As a resource manager, I can register staff or contractors, including those without application login.
- US-2 (P0): As a team manager, I can maintain dated team membership without erasing earlier membership.
- US-3 (P0): As an authorized reader, I can find resources and teams without receiving restricted personal details.

## Acceptance criteria
- **AC-01:** Given resource-manage permission, I can create a resource without a login account; this does not create a Django user or grant application access.
- **AC-02:** Given a valid same-organization membership, linking it to a resource succeeds; cross-organization or duplicate live linkage fails.
- **AC-03:** Given a membership is suspended, its resource identity and historical team/work references remain; resource retirement does not automatically delete a user.
- **AC-04:** Given a team assignment starts and ends, as-of-date queries include it only in that interval; end must be later than start.
- **AC-05:** Given an overlapping assignment to the same team/resource pair, the write is rejected even under concurrent requests; different teams may overlap if D-022 is accepted.
- **AC-06:** Given an archived team or retired resource, new assignments are refused while prior memberships remain available to authorized readers.
- **AC-07:** Given resource-read without sensitive-contact permission, list/detail/API responses omit email and phone; unauthorized organization queries reveal nothing.
- **AC-08:** Given a stale edit or unauthorized relink, no partial changes occur and authorized changes record actor, reason and previous linkage.

## Operations, actors and data ownership
The `resources` module owns this feature. Operation/actor mapping is enumerated
in [design.md](design.md). Named permissions are proposed capability keys, not
approved job titles. Organization scope is mandatory for business data; personal
account data is explicitly self-scoped. Personal data must not appear in generic logs.

## Domain invariants
Resource identity, employment, organization membership and project allocation are separate. Resource status is not a billing flag. Proposed team intervals use business dates [start,end); null end means ongoing. A resource may belong to multiple teams; a team has no automatic access-grant effect. No job title or team membership grants a role.

## Dependencies
0003 memberships, 0004 resource/team permissions. Allocation/capacity calculation remains later work.

## Non-functional requirements
Permission refusal must occur server-side and stale edits must not overwrite newer data.
Lists must be bounded; latency/dataset targets need D-012 approval. Screens must be
keyboard-operable with visible focus, labels and announced errors; use existing themes.
Retention and audit access require D-013 resolution for production. Business dates and
timestamps have different semantics; user timezone never rewrites stored work.

## Edge cases
Cross-tenant IDs, inactive actor, concurrent edits, duplicate submission, empty lists,
network loss after a write, stale organization requests and archived references.
On an uncertain mutation outcome refresh authoritative state before retry; do not
blindly replay an action. Feature-specific cases are captured in ACs above.

## Out of scope
Salary, leave, payroll, attendance sync, skills catalog, work calendars, capacity calculation, allocation, billing rates and historical correction UI.

## Open decisions — implementation blockers
D-022: confirm contractor/no-login resources, multi-team membership and whether resource-to-membership linking may be changed. Recommended: support no-login resources, multi-team membership, privileged link/end operations with history. No automatic matching by email. Retroactive team corrections affecting issued reports require a later correction policy; first slice allows prospective start/end changes only.

D-024 covers shared concurrency/revocation semantics; D-012/D-013 cover workload
and retention policy. The owner may revise the proposed slice before implementation.

## Change log
| Date | Change | Authority |
| --- | --- | --- |
| 2026-10-18 | Initial draft for morning review | Owner requested multiple SDD drafts only |
