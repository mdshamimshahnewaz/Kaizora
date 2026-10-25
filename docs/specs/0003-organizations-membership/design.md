# Design — 0003 Organizations & Membership

Status: Implemented technical baseline under the owner’s “Please implement” instruction.
Date: 2026-10-18 · Constitution: 1.1 · Implementation authorised: Yes (2026-10-18).
All new product choices and API/data shapes below are PROPOSED unless inherited from the constitution.

[Specification](spec.md) · [Tasks](tasks.md) · [Verification plan](verification.md)

## Ownership and dependencies
Owner: `organizations`. Existing 0002 authentication; 0004 is required before general membership-management UI is enabled.

## Data model and constraints
Organization(id UUID, name, timezone, status, version); Membership(id UUID, organization_id, user_id, status, is_owner, version, joined_at); MembershipStatusEvent and OrganizationChangeEvent (actor, reason, timestamp, transition). Unique (organization_id,user_id); indexes (user_id,status) and (organization_id,status,id). Identity user reference is protected from cascading deletion. is_owner is a reserved bootstrap capability, not an ordinary editable role.

## Public interfaces and transaction boundary
Proposed signatures describe contracts, not implemented functions. Scope DTOs carry
actor, organization and membership IDs; they are never a permanent permission grant.
resolve_scope(actor_id, organization_id) -> ActiveScopeDTO; list_my_organizations(actor_id, page) -> PageDTO; get_membership(scope, membership_id) -> MembershipDTO; change_membership(actor_id, organization_id, command) -> MembershipDTO. Organization commands validate active scope themselves. Ordinary management policy is supplied by a lazily registered policy callback/port from 0004; no callback means deny. Reserved bootstrap/owner transfer uses organizations-owned invariants. Never trust a caller-created authorization boolean.
Commands own atomic writes; downstream modules receive frozen DTOs only.

## API contracts
| Method | Path | Actor / permission | Request | Success / specific error |
| --- | --- | --- | --- | --- |
| GET | /api/v1/organizations/ | Signed-in user | page | 200 paginated {id,name,timezone,membership_id} |
| POST | /api/v1/organizations/ | Bootstrap operator only | {name,timezone,owner_user_id} | 201 organization; 400 invalid; 403 forbidden |
| GET | /api/v1/organizations/{org}/ | Active member | — | 200 organization snapshot |
| GET | /api/v1/organizations/{org}/memberships/ | memberships.read | page,status | 200 paginated memberships |
| POST | /api/v1/organizations/{org}/memberships/ | memberships.manage; 0004 | {user_id} | 201 membership; 409 duplicate |
| PATCH | /api/v1/organizations/{org}/memberships/{id}/ | memberships.manage; owner invariant | {status,reason,version} | 200 updated; 409 stale/last owner |
| POST | /api/v1/organizations/{org}/transfer-owner/ | Current owner | {target_membership_id,version,reason} | 200 ownership snapshot; 409 conflict |

Response records expose stable IDs, permitted fields from the model section and version;
exclude private event records, secrets and fields without read permission. Timestamp
fields are ISO 8601 with offset. Define final serializer examples once owner decisions
are resolved; these draft contracts must not be treated as generated OpenAPI.

## Frontend behaviour
Organization selector in the existing shell, organization settings and member list under /app/o/:orgId/settings. No-membership screen explains that access must be provisioned; it does not invent a default organization. Account and logout remain available. Manager UI waits for 0004. Organization is explicit in route and API, not a mutable global backend session field.
Use typed feature API wrappers, not component-level ad-hoc fetch. Loading, empty,
validation, conflict, denied and unavailable states must be separately reviewable.

## Alternatives and decisions
CONFIRMED (D-018, owner feature approval 2026-10-18): support multiple memberships in the data model, with one selected organization per browser view. Start with operator-provisioned organizations and existing Django users; email invitation/acceptance remains a separate later feature. Reserved ownership must preserve at least one active owner. Staff status does not automatically confer organization ownership. Detailed capability/delegation rules remain in feature 0004 and technical design decisions remain subject to review.

## Feature risks
The bootstrap and policy integration can create an authorization bypass if handled as a frontend check. Keep manager operations fail-closed until 0004. Last-owner locks serialize per organization. Historical event retention and access must be agreed before deployment.

## Shared contract conventions (proposed for this batch)
All routes use JSON and existing Django session/CSRF behaviour; native auth is not added.
Anonymous requests follow existing SessionAuthentication semantics (typically 403).
An inaccessible organization or scoped object returns 404 without existence disclosure;
a visible object with a forbidden action returns 403. Invalid input is 400; stale version,
uniqueness or lifecycle conflict is 409. No shared error-envelope migration is implied:
use a documented `detail` string for conflicts and serializer field errors for validation.
Lists use `{count,next,previous,results}`, 50 default/100 maximum, validated positive page,
allow-listed ordering ending in id, and reject unknown filter/sort keys with 400.
Search is trimmed, maximum 100 characters; indexed fields and representative data must
be profiled before scale claims. List contracts do not expose totals outside visible scope.
UUID IDs are opaque. Mutable records have integer version starting at 1; commands compare
expected version atomically and increment once. Unknown write fields are rejected, not
silently ignored. Omitted patch fields are unchanged; null is allowed only where specified.
Names/codes: name <=200 characters; code <=32, normalized case-insensitively within org;
plain-text description <=4000. Exact policy approval belongs to each feature decision.
No bulk API, DELETE or unrestricted export is introduced. OpenAPI/type updates ship with
implementation, never with these design drafts.

## Audit and migration approach
Each owning module stores its change events atomically with writes (actor ID, organization,
entity ID, action, UTC timestamp, reason and minimal permitted change details). These are
internal records, not a new global audit UI; future audit module may consume events through
interfaces. No generic logging subsystem or queue is assumed. Retention/access policy is
D-013; app-level immutability is not a claim of database-admin tamper proofing.
Use additive migrations and protected historical references; migration rehearsal covers
fresh and existing PostgreSQL installations. Never assign tenants or roles to all users
implicitly. Data-bearing rollback requires export/backup and explicit migration planning;
do not drop populated tables as an automatic rollback. Preserve 0002 session contract.

## Verification strategy and non-functional targets
Plan PostgreSQL integration tests for constraints, transaction rollback and concurrency;
unit/interface tests for policy; frontend interaction tests for loading/error/denial and
browser checks for narrow layout, keyboard and light/dark. API tests must call endpoints
without relying on hidden buttons. Regenerate OpenAPI/types and run existing auth/health/
boundary regression checks during implementation. No tests are executed at planning time.
D-012 remains OPEN: proposed benchmark is 100k records in the owning high-volume table,
10 organizations and 20 concurrent list readers; target p95 <500 ms server latency for
bounded indexed lists on an agreed environment. This is a candidate acceptance budget,
not measured performance or a promised SLA. Record query counts/plans and payload sizes.
Permission changes take effect on the next request begun after commit; concurrent in-flight
writes require a documented linearization/lock policy before implementation (D-024).

## Constitution and alternatives
P1/P2: draft status, decision IDs and AC/task mapping; P3/P4: explicit owner interfaces,
transaction owner and shared DRF contract; P5: scope/permission checks and no secrets;
P6: preserve historical identity; P7: custom-field storage is deferred to D-009 instead
of ad-hoc JSON added in each module; P8: planned evidence and migration limits;
P9: existing React/Vite/shadcn design system. A universal workflow engine, internal HTTP,
Redis permission cache and new frontend framework are not needed for this first slice.

## Acceptance traceability
| AC | Design coverage | Tasks | Planned evidence |
| --- | --- | --- | --- |
| AC-01 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-01: Operator succeeds; non-operator denied; rollback on owner creation failure. |
| AC-02 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-02: Three-organization fixtures; list/detail/direct-interface denial. |
| AC-03 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-03: Deactivate then replay request; verify historical fixture still references the same membership. |
| AC-04 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-04: Two PostgreSQL transactions attempting last-owner removal/transfer. |
| AC-05 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-05: Duplicate and reactivation tests; old events remain unchanged. |
| AC-06 | Frontend behaviour and API contracts | T-03, T-04, T-05 | V-06: Controlled delayed responses, organization switch, scoped cache invalidation. |
| AC-07 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-07: Permission, stale version and event atomicity tests. |
| AC-08 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-08: Fresh and upgrade migration fixtures; no implicit membership backfill. |

## Definition of implementation readiness
D-018 product direction is approved. Resolve relevant upstream contracts and D-024; finalize endpoint examples
and capability matrix. Owner authorizes implementation separately. Design remains a
review draft until then; all new model/API names may change during review.

## Implementation resolutions — 2026-10-18

- Operator authorization is the Django permission `organizations.bootstrap_organization`;
  active superusers satisfy it. Staff alone does not. This permission grants provisioning,
  never membership or tenant read access. API and `provision_organization` command share
  the same command. Organization Admin and event records are read-only.
- `ORGANIZATIONS_PERMISSION_POLICY` is an optional callable import path owned by the
  future composition configuration. Absent policy denies membership read/manage, even
  for owners. It is NOT configured in production by this feature. Tests install a local
  owner policy solely to verify the commands; that policy is not shipped as an app grant.
- Owner transfer is a reserved command and requires current active owner membership.
  Its version is the organization version; membership patches use membership version.
  Transfer promotes an active target then demotes the initiating owner in one transaction.
  It does not require the target to already be an owner (clarifies AC-04 wording).
- Organization-row locks serialize all membership mutations and owner transfers. Scope
  is re-read after acquiring the lock. Requests begun after a committed revocation fail;
  reads already in flight may complete. Future business mutations must specify their
  own matching lock/revalidation semantics. D-024 is resolved for this feature only.
- UI selects organizations via the Organizations navigation/chooser and explicit
  `/app/o/:orgId/settings` route. Settings are read-only. Changing organizations or
  authenticated identity remounts scoped content; aborted/late requests cannot replace it.
  Focus/60-second checks remove private content when access is lost.
- Pagination supports page/page_size (50 default, 100 max), with bounded queries and
  stable ordering. Membership list additionally accepts status. Unsupported/repeated
  query keys and unknown input fields are rejected. No search/sort endpoint was added.
- Actual serializers and generated OpenAPI define final response shapes. Field validation
  may use DRF field errors; conflict responses use detail. Organization creation returns
  null membership_id/is_owner false when the operator is not the chosen owner.
- Existing Django user deactivation is global administration outside membership commands;
  it may make an owner unable to sign in. Reactivate that account through the existing
  operator recovery path. No new bypass that reads tenant data or assigns ownership was
  introduced. Membership commands preserve the last active owner; arbitrary ORM/SQL
  and global account administration are not claimed to be protected by those commands.
- D-012 load benchmark and D-013 production retention remain unapproved/unexecuted.
  No measured scale claim is made. No dependencies were installed or upgraded.


## 0004 integration follow-up — 2026-10-18

The owner approved 0004 in full and requested completion of 0003 afterward. Its live
permission policy now governs member reads/add/status commands. Organization settings
include member addition by existing exact username, suspend/end/reactivate, and owner
transfer with reason/version checks. Stable membership identities and historical events
remain unchanged. No implicit organization or role grants were seeded. Non-owner managers
cannot change an owner's membership status. CLI provisioning accepts operator/owner UUIDs
or exact usernames. See [0004 verification](../0004-roles-permissions/verification.md) for
this follow-up's tests, UI checks and limits; earlier implementation limits are historical.


## UI/Admin provisioning correction — 2026-10-18

Owner clarified: “BHai ami to UI and admin theke eisob banaite chai”. This supersedes
previous CLI-first/read-only-Admin delivery choices. App Organizations now has a
permission-gated creation form; creation accepts either owner_user_id or owner_username.
GET `/organizations/provisioning/` returns only the current actor's can_create boolean.
Django Admin supplies organization creation/owner transfer, member add/status change,
role creation/edit/archive and assignment create/revoke forms. They call the same atomic
commands; no ModelAdmin save can directly overwrite membership ownership or grants.
Admin entry requires staff; domain authority is still membership/role scoped. Events/raw
permission rows remain read-only. Existing-user account creation remains Django UserAdmin.
No new business capability or automatic tenant bypass was added. No model migration needed.
