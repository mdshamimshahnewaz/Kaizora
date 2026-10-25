# Kaizora decision register

Updated: 2026-10-18. CONFIRMED means supported by existing user direction or an
implemented baseline, with provenance below; it does not mean a new owner sign-off.
PROPOSED requires review before it becomes a product commitment. OPEN blocks dependent
work. DEFERRED is explicitly outside current scope. Record later changes as new rows
that supersede an ID; do not erase history. Feature-specific detail stays in its spec.

| ID | Status | Decision / question | Basis / next action |
| --- | --- | --- | --- |
| D-001 | CONFIRMED | Django/DRF, React/Vite, PostgreSQL modular monolith | User stack request; existing manifests; ADR 0001 |
| D-002 | CONFIRMED | Public module interfaces; same-process calls; shared web/mobile HTTP API | User architectural direction; constitution P3–P4 |
| D-003 | CONFIRMED | Effective-dated allocations/rates and immutable historical attribution | User's TaskBridge history problem; existing constitution |
| D-004 | CONFIRMED | shadcn/Tailwind/Lucide visual foundation | User-approved UI stack and current frontend |
| D-005 | CONFIRMED | Web username/password Django sessions, CSRF; no browser-stored auth token | Implemented feature 0002; not a mobile auth decision |
| D-006 | CONFIRMED | Generated OpenAPI and TypeScript types | Existing schema and generation scripts |
| D-007 | CONFIRMED | Adapt Timely documentation structure using Kaizora stack and existing paths | Owner request, 2026-10-18; no runtime changes |
| D-008 | OPEN | Organisation model, membership, roles, object/field permissions | Resolve before business APIs; suggested next feature |
| D-009 | OPEN | Custom field types, storage, scope, versioning and indexed queries | Resolve in customization design; no JSON/EAV choice assumed |
| D-010 | OPEN | Replacement approvals, overlapping coverage and billing attribution policy | Resolve in allocations/replacements/commercials specs |
| D-011 | OPEN | Currency, rounding, tax, period close and adjustment policy | Resolve before billing implementation |
| D-012 | OPEN | Performance budgets, representative dataset size and concurrency | Set measurable targets per business feature |
| D-013 | OPEN | Audit events, retention, erasure and access-revocation targets | Resolve per sensitive feature and deployment |
| D-014 | DEFERRED | Native mobile OAuth/OIDC, refresh/revocation and device storage | Dedicated identity design before mobile app |
| D-015 | DEFERRED | Shared throttle cache, proxy trust, backups, monitoring and production deployment | Required production design; local cache is current limitation |
| D-016 | PROPOSED | Unified error envelope/request IDs and common list/filter policy | Current DRF errors remain; needs compatibility design |
| D-017 | DEFERRED | Background jobs, realtime, caches and service extraction | Add only for measured or durable-work requirements |

No Entra, ORBIS, UNIS, Next.js or Timely role decision is inherited.

## Basic-module planning batch — 2026-10-18

The initial request authorized drafting only. On 2026-10-18 the owner approved
feature 0003 and its D-018 product direction; other proposals and implementation
remain unapproved.
These refine D-008 and preserve its OPEN state. Full context lives in feature specs.

| ID | Status | Decision needed | Recommendation for review / dependent feature |
| --- | --- | --- | --- |
| D-018 | CONFIRMED | Multi-organization membership, provisioning and reserved owner powers | Support multiple memberships; operator creates organization/first owner; existing-user enrollment first; invitations later; preserve an active owner; staff has no automatic ownership. Owner: “OKay 003 features approved”, 2026-10-18. Technical design remains draft. |
| D-019 | CONFIRMED | Initial role/capability matrix and delegation rules | Additive grants/default deny; reserved ownership; prevent granting beyond delegated powers. 0004 |
| D-020 | OPEN | Self-editable account fields and preference persistence | First/last name plus theme/timezone; no email/username/password changes in this slice. 0005 |
| D-021 | OPEN | Client identifiers and contact access | Organization-unique immutable client code; contact read/manage separate from client read/manage. 0006 |
| D-022 | OPEN | Resource identity/linking and team membership | Resources may have no login; multiple teams; privileged dated linkage; prospective changes first. 0007 |
| D-023 | OPEN | Project visibility, client requirement, creator access and lifecycle | Private by default; optional client for internal projects; explicit initial manager grant; no automatic staffing/billing. 0008 |
| D-024 | PROPOSED | Shared draft contract/concurrency policy | Bounded 50/100 lists, version conflicts, explicit organization paths; live access checks; define revocation linearization and final serializer examples before implementation. All six drafts |

D-012 performance and D-013 audit/retention remain unresolved; proposed draft budgets
are not measured or approved SLAs. Customization is still D-009, not silently added
to client/resource/project tables.

## 0003 implementation — 2026-10-18

Owner instruction “Please implement” authorized feature 0003. Implementation resolutions
are recorded in its design.md: named Django provisioning permission, no tenant read bypass,
default-deny future membership-policy port, organization-row locking and version checks,
explicit frontend organization routes and stale-response isolation. D-024 is resolved for
these endpoints only; its broader cross-feature policy remains proposed. D-008/0004 role
catalog, D-012 workload targets and D-013 production retention remain open.


## 0004 and 0003 integration — 2026-10-18

Owner: “0004 full approved, ekhon implement kore dao and then sesh hole 0003 o kore amake janao.”
D-019 is confirmed: static catalog, reserved owner, additive custom roles, live evaluation,
same-scope delegation bounded by current grants, explicit presets with no automatic grants.
The final matrix and project resolver contract are in 0004/design.md. D-024 is implemented
for 0003/0004 with the shared organization mutation lock and optimistic versions. 0003's
previous default-deny port is now wired to this policy and its member management UI is enabled.
D-012/D-013 and 0005–0008 remain unresolved/unimplemented; this does not approve those drafts.


## 0005–0008 implementation — 2026-10-18 (supersedes earlier draft state)

Owner explicitly requested implementing 0005 through 0008 in App UI and Django Admin,
reserving acceptance for a later full-flow UI/UX review. D-020–D-023 are adopted for
this implementation, and D-024 is implemented across these features with current
permission checks, bounded API lists, shared organization mutation locks and optimistic
revisions (account mutations lock the user). Exact choices and executed evidence are
in [the delivery record](specs/0005-0008-delivery.md). These supersede the OPEN/PROPOSED
implementation states above; they do not record final owner UI/UX acceptance.
D-012 production performance and D-013 retention remain open.


## D-025 — Simple resource selection (2026-10-18)

Owner requested avoiding duplicate User/Person setup and searchable user dropdowns, while supporting workers without system login. Existing organization members can be selected directly for teams/project workforce; resource identities are derived/reused atomically. No-login workers remain independent resources. Workforce membership grants no app/project access and is separate from future task/time/billing workflows. Implemented as feature 0009; owner UX acceptance pending.
