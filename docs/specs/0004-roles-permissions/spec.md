# 0004 — Roles & Permissions

Status: Implemented — approved scope; verification and owner acceptance remain separate.
Date: 2026-10-18 · Constitution: 1.1 · Implementation authorised: Yes — owner: “0004 full approved”, 2026-10-18.
The owner approved this feature in full and requested implementation, followed by 0003 integration. Final implementation resolutions below govern over earlier proposal wording.

## Problem and scope
Define explicit server-enforced capabilities for organization and project actions. UI visibility follows permissions, but changing the UI must never grant access.

## User stories
- US-1 (P0): As an owner, I can assign restricted capabilities to active members.
- US-2 (P0): As a member, I see available actions and receive server denial for forbidden actions.
- US-3 (P0): As an owner, I can revoke access without rewriting historical work or waiting for the next login.

## Acceptance criteria
- **AC-01:** Given no matching grant, an organization action is denied; Django staff/superuser status alone does not grant business access through public APIs.
- **AC-02:** Given an authorized owner, creating a role with known permission keys succeeds; unknown keys, foreign membership IDs and cross-organization role assignment are rejected.
- **AC-03:** Given a grant is removed, the next protected request is denied; a previously rendered button cannot perform the operation.
- **AC-04:** Given a non-owner role manager, assigning a role containing capabilities outside their delegable set is rejected; owner transfer is not represented as a grantable key.
- **AC-05:** Given an archived role or inactive membership, related grants convey no access while their history remains readable to authorized reviewers.
- **AC-06:** Given a member requests their effective capabilities, only their selected organization capabilities are returned and no other user grants leak.
- **AC-07:** Given a permission change conflicts with another edit, one update succeeds and the stale update returns conflict without a partial grant set.
- **AC-08:** Given a project-scoped check, the access evaluator requires explicit project context; the supplied context alone cannot create a grant.

## Operations, actors and data ownership
The `identity` module owns this feature. Operation/actor mapping is enumerated
in [design.md](design.md). Named permissions are proposed capability keys, not
approved job titles. Organization scope is mandatory for business data; personal
account data is explicitly self-scoped. Personal data must not appear in generic logs.

## Domain invariants
CONFIRMED: allow-list permission keys with additive grants and default deny; no explicit deny rules in v1. Organization owner is a reserved invariant from 0003, not a mutable user role. Project grants never become organization-wide grants. Membership deactivation overrides all grants. No permission embedded in long-lived frontend state can override live backend checks.

## Dependencies
0003 scope and membership contracts. Implement its policy port without introducing organizations -> identity -> organizations imports.

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
SSO/Entra, platform support impersonation, arbitrary policy scripting, per-record ACL builder, custom-field permissions editor, full audit explorer.

## Approved decisions and remaining production work
D-019 is confirmed by full feature approval. Reserved owner plus configurable organization/project role definitions; exact catalog and preset matrix are recorded in design.md and implemented in identity/catalog.py. Project-scoped grants wait for 0008. Field-level permissions for custom fields wait for customization; sensitive fields remain excluded until specified.

D-024 covers shared concurrency/revocation semantics; D-012/D-013 cover workload
and retention policy. The owner may revise the proposed slice before implementation.

## Change log
| Date | Change | Authority |
| --- | --- | --- |
| 2026-10-18 | Initial draft for morning review | Owner requested multiple SDD drafts only |

| 2026-10-18 | Full 0004 approval, implementation and 0003 policy/UI integration | Owner: “0004 full approved, ekhon implement kore dao and then sesh hole 0003 o kore amake janao.” |
