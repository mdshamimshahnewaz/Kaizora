# Design — 0004 Roles & Permissions

Status: Implemented — approved scope; verification and owner acceptance remain separate.
Date: 2026-10-18 · Constitution: 1.1 · Implementation authorised: Yes — owner: “0004 full approved”, 2026-10-18.
The owner approved this feature in full and requested implementation, followed by 0003 integration. Final implementation resolutions below govern over earlier proposal wording.

[Specification](spec.md) · [Tasks](tasks.md) · [Verification plan](verification.md)

## Ownership and dependencies
Owner: `identity`. 0003 scope and membership contracts. Implement its policy port without introducing organizations -> identity -> organizations imports.

## Data model and constraints
identity owns PermissionCatalog (code registry), OrganizationRole(id,organization_id,name,status,version), RolePermission(role_id,key), RoleAssignment(id,organization_id,membership_id,role_id,started_at,ended_at) and immutable grant-change events. Unique live assignment and organization-scoped role name. Project-specific role assignment will be owned by projects in 0008, not written by identity. Index assignments by organization/membership/live status.

## Public interfaces and transaction boundary
Proposed signatures describe contracts, not implemented functions. Scope DTOs carry
actor, organization and membership IDs; they are never a permanent permission grant.
authorize(scope, permission_key, resource_context=None) -> None or PermissionDenied; get_effective_permissions(scope) -> frozen PermissionSetDTO; assign_role(scope, command) -> AssignmentDTO; get_role_permissions(scope, role_id) -> frozen PermissionSetDTO. Identity resolves/validates membership using organizations.interfaces. A composition-root registration wires the organizations policy port to identity authorize; organizations never imports identity internals. Project services pass validated owned project grants/context; evaluator checks them against the catalog and org-scoped roles.
Commands own atomic writes; downstream modules receive frozen DTOs only.

## API contracts
| Method | Path | Actor / permission | Request | Success / specific error |
| --- | --- | --- | --- | --- |
| GET | /api/v1/organizations/{org}/permissions/me/ | Active member | — | 200 {organization_id,permissions:[key]} |
| GET | /api/v1/organizations/{org}/roles/ | roles.read | page | 200 paginated roles |
| POST | /api/v1/organizations/{org}/roles/ | roles.manage + delegation limit | {name,permissions:[key]} | 201 role |
| PATCH | /api/v1/organizations/{org}/roles/{id}/ | roles.manage + delegation limit | {name?,permissions?,status?,version,reason} | 200 role; 409 stale |
| POST | /api/v1/organizations/{org}/role-assignments/ | roles.assign + delegation limit | {membership_id,role_id,reason} | 201 assignment; 409 duplicate |
| POST | /api/v1/organizations/{org}/role-assignments/{id}/revoke/ | roles.assign | {reason,version} | 200 ended assignment |

Response records expose stable IDs, permitted fields from the model section and version;
exclude private event records, secrets and fields without read permission. Timestamp
fields are ISO 8601 with offset. Define final serializer examples once owner decisions
are resolved; these draft contracts must not be treated as generated OpenAPI.

## Frontend behaviour
Role list/editor and assignment dialog under organization settings; read-only effective permission summary for own account. Hide unavailable actions but handle denial on click. Warn about effects of role changes; never claim custom-role editing exists before these endpoints do. Project actions are displayed only after project-scoped resolution.
Use typed feature API wrappers, not component-level ad-hoc fetch. Loading, empty,
validation, conflict, denied and unavailable states must be separately reviewable.

## Alternatives and decisions
D-019: confirm initial roles, exact capability matrix and who may delegate which keys. Recommended owner plus configurable organization roles; no hardcoded universal employee/manager role assumptions. Review an explicit permission catalog before implementation. Project-scoped grants wait for 0008. Field-level permissions for custom fields wait for customization; sensitive fields remain excluded until specified.

## Feature risks
Roles are an escalation surface. Adopt the simple additive model only after owner review; never ship a permissive fallback. Uncached permission evaluation is the baseline; adding caching later requires a documented invalidation/revocation contract.

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
| AC-01 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-01: Permission allow/deny matrix including staff without membership. |
| AC-02 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-02: Unknown permission and forged role/membership tests. |
| AC-03 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-03: Revoke and replay request without login refresh. |
| AC-04 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-04: Privilege escalation, self-grant and reserved capability tests. |
| AC-05 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-05: Role archive and member suspension tests. |
| AC-06 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-06: Self-summary scoped response and UI tests. |
| AC-07 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-07: Concurrent role edits with version and transaction tests. |
| AC-08 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-08: Project grant deny/allow tests using 0008 contract fixtures. |

## Definition of implementation readiness
Resolve D-019, relevant upstream contracts and D-024; finalize endpoint examples
and capability matrix. Owner authorizes implementation separately. Design remains a
review draft until then; all new model/API names may change during review.

## Capability scope contract for owner review
Separate permission catalog metadata from role assignment scope. Catalog entries declare
organization-only versus project-applicable keys. Organization roles may grant
memberships.read/manage, roles.read/manage/assign, clients.read/manage,
contacts.read/manage, resources.read/manage/link_identity/contact_read,
teams.read/manage, projects.create/read_all and explicitly approved project keys.
Project-scoped assignments can include only projects.read/manage/transition/reopen/
restore/access.read/access.manage; organization administration keys are rejected there.
Project role capabilities are evaluated against the current catalog, not trusted from
an arbitrary caller payload. A per-project role may not confer projects.create/read_all.

Approved initial preset direction: organization owner (reserved), organization
administrator (explicit reviewed key set, never ownership transfer), member (own account
and organization identity only), and project manager (project-scoped keys only). Custom
role design must decide whether a role is organization or project scoped; add scope_kind
to OrganizationRole and make it immutable after assignment. A manager may delegate only
keys they themselves may delegate in the same scope. Owner transfer remains 0003.
These definitions require D-019 acceptance; no default grants are silently assigned.


## Final implementation resolutions — 2026-10-18

Authority: full owner approval of 0004 and instruction to finish 0003 afterward.
D-019 is resolved for this slice. This section supersedes draft alternatives above.

- The static catalog is `backend/modules/identity/catalog.py`. Organization keys are
  memberships.read/manage, roles.read/manage/assign, clients.read/manage,
  contacts.read/manage, resources.read/manage/link_identity/contact_read,
  teams.read/manage, projects.create/read_all. Project-applicable keys are
  projects.read/manage/transition/reopen/restore/access.read/access.manage.
- Reserved owners hold all catalog capabilities in their organization; ownership transfer
  remains a separate owner-only command. Staff/superuser alone grants no business access.
- Presets are templates, never silent assignments: Organization administrator includes all
  catalog keys; Member includes no extra keys; Project manager includes the seven project
  keys only. Basic account and organization identity reads require active membership, not a role.
- A non-owner may create/change/assign/revoke only keys they currently hold in this org.
  Editing/archiving a higher-powered role is also denied (both old and new key sets checked).
  Grants are additive; no deny rules. Archiving suppresses live assignments; restoring the
  role restores them. Suspension/end suppress membership grants; reactivation restores any
  non-revoked grants. Revoke ends an assignment; a later grant creates a new history row.
- Role names are case-insensitively unique per org; roles have immutable scope_kind.
  Project definitions may be prepared now; organization assignment rejects project roles.
- Identity's public interface uses organizations' public scope/lock/target interfaces.
  Organizations' identity lookup and authorization ports are wired with settings at the
  composition root. Organizations imports no identity module, avoiding a Python import cycle.
- `authorize(scope, key, resource_context=project_uuid)` calls the configured trusted
  `IDENTITY_PROJECT_SCOPE_RESOLVER(actor_id, organization_id, project_uuid)` for project keys.
  It must resolve actual project visibility/membership and return `ProjectScopeDTO` with
  matching org/project/membership and current project role IDs. Identity reads each role's
  current catalog keys/status itself. No resolver is registered before 0008; project checks
  deny even for owners. Caller-supplied permissions or fake context objects cannot grant access.
- D-024 for 0003/0004: mutation commands acquire the same organization row lock before
  membership/permission/version checks. Role edit, grant, revoke, membership status and
  transfer therefore serialize within an org. Version mismatch returns 409. Reads started
  after commit see live state; an already-running read may finish using its prior snapshot.
  Direct SQL/admin global user deactivation is an operator concern outside this lock contract.
- Audits are atomic with writes. Role-change events retain old/new permission snapshots;
  assignment rows retain start/end times and version. Admin role/grant/event pages are read-only.
  This is app-level protection, not protection against database administrators.
- Shared transport errors, strict input validation and bounded pagination now live in
  `backend/common/api.py`; no domain model is exported through it.

### Final endpoint additions and example

The API table above is implemented. Also GET `permissions/catalog/` returns approved keys
and presets for active members, and GET `role-assignments/` returns bounded assignment history
under roles.read. GET permissions/me includes membership_id and is_owner as well as keys.
PATCH requires version and reason even though generated OpenAPI PATCH properties are optional.
Membership add accepts exactly one existing active user_id or exact username; it does not
create accounts or expose a global search directory. Membership read includes username and
display_name. Lists remain 50 default/100 max, stable ordering, no unbounded fetch.

```json
{"name":"Member reader","scope_kind":"organization","permissions":["memberships.read"]}
```

POST roles returns id/name/scope_kind/status/version/permissions. Update uses, for example,
`{"version":1,"reason":"End directory access","permissions":[]}`. Assignment uses
`{"membership_id":"<uuid>","role_id":"<uuid>","reason":"Assigned support duties"}`.
Revoke uses `{"version":1,"reason":"Duties ended"}`. Complete shapes are generated in
`docs/api/openapi.yaml`; the frontend consumes generated types via feature wrappers.

The UI lives under organization settings: own permission summary, paginated members,
role editor/presets, and assignment history. Assign selection uses the current Members and
Roles pages (requires both read permissions); write-only API grants remain independent.
Mutations use fresh CSRF, clear stale state and refresh after failures, never automatic replay.
Ownership transfer warns the source owner about losing reserved authority.

No production grants or example organizations were seeded. Additive identity.0002 was
applied to the configured local DB after reviewing the migration plan. No server was started.


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
