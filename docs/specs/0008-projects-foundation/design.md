# Design — 0008 Projects Foundation

> Implementation update (2026-10-18): the owner authorized 0005–0008 in App UI and Django Admin. [Delivery decisions and evidence](../0005-0008-delivery.md) supersede the original draft-only labels below. Owner UI/UX acceptance is still pending.

Status: Implemented — owner UI/UX acceptance pending.
Date: 2026-10-18 · Constitution: 1.1 · Implementation authorised: Yes, by the owner on 2026-10-18.
Original planning detail is retained below; the delivery record documents adopted decisions, actual contracts and verification limits.

[Specification](spec.md) · [Tasks](tasks.md) · [Verification plan](verification.md)

## Ownership and dependencies
Owner: `projects`. 0003 scope, 0004 policy, 0006 client DTOs. 0007 resource data is optional for future allocation, not required for project access membership.

## Data model and constraints
Project(id UUID,organization_id,code,normalized_code,name,type,status,client_id nullable,description,start_date nullable,target_end_date nullable,version); ProjectAccess(id,organization_id,project_id,membership_id,role_id,started_at,ended_at,version); ProjectChangeEvent/AccessEvent. Unique org/code and unique live project/member/role grant. Index org/status/type/id and project/member/live. Organization ID cannot change after creation. Store descriptions as plain text in first slice.

## Public interfaces and transaction boundary
Proposed signatures describe contracts, not implemented functions. Scope DTOs carry
actor, organization and membership IDs; they are never a permanent permission grant.
get_project_context(scope, project_id, permission) -> ProjectContextDTO; list_visible_projects(scope, query) -> PageDTO; create_project(scope, command) -> ProjectDTO; transition_project(scope, command) -> ProjectDTO; grant_project_access(scope, command) -> AccessDTO. Projects validates owned access rows and invokes identity evaluator with verified role DTOs; identity never queries projects tables. Use clients.interfaces for client validity. Creation owns transaction and calls a locking active-client validation interface in the same DB transaction; lock order client then project. No resource allocations are written.
Commands own atomic writes; downstream modules receive frozen DTOs only.

## API contracts
| Method | Path | Actor / permission | Request | Success / specific error |
| --- | --- | --- | --- | --- |
| GET | /api/v1/organizations/{org}/projects/ | projects.read scoped / projects.read_all | page,search,status,type,client_id,ordering | 200 paginated visible projects |
| POST | /api/v1/organizations/{org}/projects/ | projects.create | {code,name,type,client_id?,description?,start_date?,target_end_date?} | 201 project |
| GET | /api/v1/organizations/{org}/projects/{id}/ | Scoped projects.read | — | 200 project; 404 missing/inaccessible |
| PATCH | /api/v1/organizations/{org}/projects/{id}/ | Scoped projects.manage | {name?,description?,start_date?,target_end_date?,version,reason} | 200 project; 409 stale |
| POST | /api/v1/organizations/{org}/projects/{id}/transition/ | Scoped projects.transition / reopen / restore | {target_status,version,reason} | 200 project; 409 invalid transition |
| GET/POST | /api/v1/organizations/{org}/projects/{id}/access/ | Scoped projects.access.read / manage | GET page; POST {membership_id,role_id,reason} | 200 list / 201 grant |
| POST | /api/v1/organizations/{org}/projects/{id}/access/{grant}/end/ | Scoped projects.access.manage | {version,reason} | 200 ended grant |

Response records expose stable IDs, permitted fields from the model section and version;
exclude private event records, secrets and fields without read permission. Timestamp
fields are ISO 8601 with offset. Define final serializer examples once owner decisions
are resolved; these draft contracts must not be treated as generated OpenAPI.

## Frontend behaviour
Projects list/create/detail at /app/o/:orgId/projects with delivery/operations badges, client selector, lifecycle action and access tab. Future tasks/time/billing tabs stay absent or visibly unavailable. No fake KPI dashboard. Empty project list distinguishes permitted creation from no access; archive/reopen actions explain consequences.
Use typed feature API wrappers, not component-level ad-hoc fetch. Loading, empty,
validation, conflict, denied and unavailable states must be separately reviewable.

## Alternatives and decisions
D-023: confirm private-by-default projects, whether internal projects may omit a client, lifecycle and initial creator access. Recommended: private projects; optional client; creator receives a project-manager role only if the role catalog explicitly defines it, otherwise creation must atomically grant an owner-selected initial manager. Role creation/assignment cannot be guessed. Client reassignment and project type changes are deferred to prevent changing financial interpretation.

## Feature risks
Project grant evaluation must not introduce cyclic module imports. Creation must not leave an inaccessible orphan project. Confirm project role/delegation rules with 0004 before implementation; prove list query scoping matches detail authorization.

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
| AC-01 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-01: Delivery/operations/internal create, duplicate and wrong/archived client tests. |
| AC-02 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-02: Private list/detail/search and forged project tests. |
| AC-03 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-03: Transition matrix and concurrent updates. |
| AC-04 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-04: Revoke/replay and history preservation. |
| AC-05 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-05: Suspended member and team-only negative cases. |
| AC-06 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-06: Archive/write denial/restore tests. |
| AC-07 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-07: Rename/reference tests and snapshot ownership review. |
| AC-08 | Frontend behaviour and API contracts | T-03, T-04, T-05 | V-08: Pagination/filter and delayed UI response tests. |

## Definition of implementation readiness
Resolve D-023, relevant upstream contracts and D-024; finalize endpoint examples
and capability matrix. Owner authorizes implementation separately. Design remains a
review draft until then; all new model/API names may change during review.

## Initial access and role-scope details
Proposed create body additionally requires `initial_manager_membership_id` and
`initial_manager_role_id` unless the owner approves an explicit creator-default rule.
Creation checks same-organization active membership and project-scoped role, then
creates Project and ProjectAccess atomically. The creator must have permission to
assign that role or creation is refused; projects.create does not imply unlimited
role delegation. Lock/recheck target membership within creation transaction.
Follow 0004 scope_kind rules: organization-only role keys cannot be attached to a
project. Access grants are checked against current role permissions on every request.
