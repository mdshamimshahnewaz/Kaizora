# 0008 — Projects Foundation

> Implementation update (2026-10-18): the owner authorized 0005–0008 in App UI and Django Admin. [Delivery decisions and evidence](../0005-0008-delivery.md) supersede the original draft-only labels below. Owner UI/UX acceptance is still pending.

Status: Implemented — owner UI/UX acceptance pending.
Date: 2026-10-18 · Constitution: 1.1 · Implementation authorised: Yes, by the owner on 2026-10-18.
Original planning detail is retained below; the delivery record documents adopted decisions, actual contracts and verification limits.

## Problem and scope
Create organization-scoped delivery projects and ongoing operations engagements with stable identity, controlled lifecycle and project-specific access. Keep staffing and financial configuration separate.

## User stories
- US-1 (P0): As a project manager with creation rights, I can create a delivery project or operations engagement.
- US-2 (P0): As an authorized project reader, I can list and open only permitted projects.
- US-3 (P0): As a project access manager, I can grant/end project access without deleting historical participation or work.

## Acceptance criteria
- **AC-01:** Given projects.create permission, a valid project is created with unique organization code, explicit type and same-organization active client or no client.
- **AC-02:** Given private project access, list and detail include only granted projects unless the user has explicit organization-wide projects.read_all.
- **AC-03:** Given an authorized lifecycle change, allowed transitions succeed; invalid transitions and stale updates fail atomically.
- **AC-04:** Given project access is ended, subsequent project reads/writes are denied while prior work and access events remain attributable.
- **AC-05:** Given an inactive organization membership, even a live project grant cannot allow access; resource/team membership alone gives no access.
- **AC-06:** Given an archived project, reads remain available under permission but ordinary edits and new grants are refused; an authorized restore is explicit.
- **AC-07:** Given a project rename or client rename, stable IDs remain; existing issued financial/report snapshots are not rewritten.
- **AC-08:** Given the user changes organization or page filters, results and request state remain scoped and bounded with no late-response leakage.

## Operations, actors and data ownership
The `projects` module owns this feature. Operation/actor mapping is enumerated
in [design.md](design.md). Named permissions are proposed capability keys, not
approved job titles. Organization scope is mandatory for business data; personal
account data is explicitly self-scoped. Personal data must not appear in generic logs.

## Domain invariants
Project access membership is not resource allocation, timesheet approval or billing eligibility. Delivery and operations are project types with shared baseline identity; operational queues/SLA come later. PROPOSED lifecycle: draft -> active -> completed -> archived; active -> archived and draft -> archived allowed; completed -> active requires reopen permission/reason; archived restore goes to draft. No implicit cascade from client archive.

## Dependencies
0003 scope, 0004 policy, 0006 client DTOs. 0007 resource data is optional for future allocation, not required for project access membership.

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
Work items, milestones/Gantt implementation, budgets/rates, project templates, custom-field values, allocations, SLA queues, client portal and billing.

## Open decisions — implementation blockers
D-023: confirm private-by-default projects, whether internal projects may omit a client, lifecycle and initial creator access. Recommended: private projects; optional client; creator receives a project-manager role only if the role catalog explicitly defines it, otherwise creation must atomically grant an owner-selected initial manager. Role creation/assignment cannot be guessed. Client reassignment and project type changes are deferred to prevent changing financial interpretation.

D-024 covers shared concurrency/revocation semantics; D-012/D-013 cover workload
and retention policy. The owner may revise the proposed slice before implementation.

## Change log
| Date | Change | Authority |
| --- | --- | --- |
| 2026-10-18 | Initial draft for morning review | Owner requested multiple SDD drafts only |
