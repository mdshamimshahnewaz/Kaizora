# 0003 — Organizations & Membership

Status: Approved — feature specification approved by project owner on 2026-10-18.
Date: 2026-10-18 · Constitution: 1.1 · Implementation authorised: Yes — owner: “Please implement”, 2026-10-18.
Approval source: “OKay 003 features approved”. This approves this feature scope and its D-018 recommendations; the subsequent “Please implement” instruction authorizes implementation within this scope.

## Problem and scope
Give each business record an explicit organization boundary and each signed-in user an explicit membership. Ending access must preserve historical identity and work references.

## User stories
- US-1 (P0): As an authorized operator, I can establish an organization and its first owner without granting all existing users access.
- US-2 (P0): As a member, I can select an organization I belong to and see only its data.
- US-3 (P0): As an authorized membership manager, I can suspend or end membership while retaining history.

## Acceptance criteria
- **AC-01:** Given an authorized bootstrap operator and an existing active user, creating an organization creates exactly one active initial owner atomically; an ordinary user cannot self-provision an organization.
- **AC-02:** Given memberships in A and B, my organization list contains only accessible organizations; a forged organization ID cannot expose C.
- **AC-03:** Given active membership, suspending or ending it denies the next protected organization request without deleting its stable membership ID or historical references.
- **AC-04:** Given another active owner exists, an owner transfer may complete; concurrent attempts cannot leave an active organization with no owner.
- **AC-05:** Given an existing membership, duplicate active membership creation is rejected; reactivation uses the same membership identity and records a new status event.
- **AC-06:** Given the user changes organization while an old request is in flight, the old response never populates the new organization view.
- **AC-07:** Given an unauthorized or stale update, no organization/membership data is changed; a successful change records actor, reason, time and before/after status.
- **AC-08:** Given a new database or an existing installation, migrations create organization tables without silently assigning every user to a tenant.

## Operations, actors and data ownership
The `organizations` module owns this feature. Operation/actor mapping is enumerated
in [design.md](design.md). Named permissions are proposed capability keys, not
approved job titles. Organization scope is mandatory for business data; personal
account data is explicitly self-scoped. Personal data must not appear in generic logs.

## Domain invariants
Organization membership grants eligibility for access, not project allocation, billability or employment. An ended membership stays referenceable by authorized historical queries. Access uses current membership state; historical work does not. CONFIRMED: one user may belong to several organizations; one active membership per user/organization, with status events. Organization deletion is excluded.

## Dependencies
Existing 0002 authentication; 0004 is required before general membership-management UI is enabled.

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
Public signup, email invitations/delivery, subscriptions, tenant deletion, project staffing, RBAC editor, cross-organization reporting.

## Approved product decisions and remaining implementation blockers
CONFIRMED (D-018, owner feature approval 2026-10-18): support multiple memberships in the data model, with one selected organization per browser view. Start with operator-provisioned organizations and existing Django users; email invitation/acceptance remains a separate later feature. Reserved ownership must preserve at least one active owner. Staff status does not automatically confer organization ownership. Detailed capability/delegation rules remain in feature 0004 and technical design decisions remain subject to review.

D-024 covers shared concurrency/revocation semantics; D-012/D-013 cover workload
and retention policy. The owner may revise the proposed slice before implementation.

## Change log
| Date | Change | Authority |
| --- | --- | --- |
| 2026-10-18 | Initial draft for morning review | Owner requested multiple SDD drafts only |
| 2026-10-18 | Feature specification and D-018 recommendations approved; design/tasks remain drafts | Owner: “OKay 003 features approved” |
| 2026-10-18 | Implementation authorised and delivered within 0003; general manager UI still depends on 0004 | Owner: “Please implement” |


## 0004 integration follow-up — 2026-10-18

The owner approved 0004 in full and requested completion of 0003 afterward. Its live
permission policy now governs member reads/add/status commands. Organization settings
include member addition by existing exact username, suspend/end/reactivate, and owner
transfer with reason/version checks. Stable membership identities and historical events
remain unchanged. No implicit organization or role grants were seeded. Non-owner managers
cannot change an owner's membership status. CLI provisioning accepts operator/owner UUIDs
or exact usernames. See [0004 verification](../0004-roles-permissions/verification.md) for
this follow-up's tests, UI checks and limits; earlier implementation limits are historical.
