# Design — 0007 People & Teams

> Implementation update (2026-10-18): the owner authorized 0005–0008 in App UI and Django Admin. [Delivery decisions and evidence](../0005-0008-delivery.md) supersede the original draft-only labels below. Owner UI/UX acceptance is still pending.

Status: Implemented — owner UI/UX acceptance pending.
Date: 2026-10-18 · Constitution: 1.1 · Implementation authorised: Yes, by the owner on 2026-10-18.
Original planning detail is retained below; the delivery record documents adopted decisions, actual contracts and verification limits.

[Specification](spec.md) · [Tasks](tasks.md) · [Verification plan](verification.md)

## Ownership and dependencies
Owner: `resources`. 0003 memberships, 0004 resource/team permissions. Allocation/capacity calculation remains later work.

## Data model and constraints
Resource(id UUID,organization_id,code,display_name,status,version); ResourceContact restricted email/phone; ResourceIdentityLink(resource_id,membership_id,started_at,ended_at,reason); Team(id,organization_id,code,name,status,version); TeamMembership(id,organization_id,team_id,resource_id,start_date,end_date,version). Stable IDs with protected references, unique org/code and live identity linkage. Store linkage history; no silent overwrite. Index org/status/name/id and team/date/resource. Interval validation uses per-resource lock and overlap query for same team pair, avoiding an unapproved PostgreSQL extension.

## Public interfaces and transaction boundary
Proposed signatures describe contracts, not implemented functions. Scope DTOs carry
actor, organization and membership IDs; they are never a permanent permission grant.
get_resource_summary(scope, resource_id, as_of=None) -> ResourceSummaryDTO; list_resources(scope, query) -> PageDTO; link_identity(scope, command) -> LinkDTO; get_team_members(scope, team_id, as_of, page) -> PageDTO; assign_team_member(scope, command) -> TeamMembershipDTO. Resources owns transactions and locks resource before same-pair interval check. Resolve membership via organizations.interfaces. Public summary excludes PII by default.
Commands own atomic writes; downstream modules receive frozen DTOs only.

## API contracts
| Method | Path | Actor / permission | Request | Success / specific error |
| --- | --- | --- | --- | --- |
| GET | /api/v1/organizations/{org}/resources/ | resources.read | page,search,status | 200 paginated summaries |
| POST | /api/v1/organizations/{org}/resources/ | resources.manage | {code,display_name} | 201 resource |
| GET | /api/v1/organizations/{org}/resources/{id}/ | resources.read; contact fields separately gated | — | 200 permitted resource fields |
| PATCH | /api/v1/organizations/{org}/resources/{id}/ | resources.manage | {display_name?,status?,version,reason} | 200 resource; 409 stale |
| POST | /api/v1/organizations/{org}/resources/{id}/identity-links/ | resources.link_identity | {membership_id,reason} | 201 link; 409 duplicate |
| POST | /api/v1/organizations/{org}/resources/{id}/identity-links/{link}/end/ | resources.link_identity | {version,reason} | 200 ended link |
| GET/POST | /api/v1/organizations/{org}/teams/ | teams.read / teams.manage | GET page,status; POST {code,name} | 200 list / 201 team |
| PATCH | /api/v1/organizations/{org}/teams/{id}/ | teams.manage | {name?,status?,version,reason} | 200 team |
| GET/POST | /api/v1/organizations/{org}/teams/{id}/memberships/ | teams.read / teams.manage | GET page,as_of; POST {resource_id,start_date,end_date?} | 200 dated list / 201 interval |
| PATCH | /api/v1/organizations/{org}/teams/{id}/memberships/{membership}/ | teams.manage | {end_date,version,reason} | 200 interval; 409 overlap/stale |

Response records expose stable IDs, permitted fields from the model section and version;
exclude private event records, secrets and fields without read permission. Timestamp
fields are ISO 8601 with offset. Define final serializer examples once owner decisions
are resolved; these draft contracts must not be treated as generated OpenAPI.

## Frontend behaviour
People and Teams lists/details at /app/o/:orgId/resources and /teams, with clear “No linked login” display. Team history has explicit as-of date. Membership changes use date fields and explain interval semantics. Retirement does not present itself as deleting historical work. Sensitive contact editor is deferred until its endpoint/retention policy is separately specified.
Use typed feature API wrappers, not component-level ad-hoc fetch. Loading, empty,
validation, conflict, denied and unavailable states must be separately reviewable.

## Alternatives and decisions
D-022: confirm contractor/no-login resources, multi-team membership and whether resource-to-membership linking may be changed. Recommended: support no-login resources, multi-team membership, privileged link/end operations with history. No automatic matching by email. Retroactive team corrections affecting issued reports require a later correction policy; first slice allows prospective start/end changes only.

## Feature risks
A link change must not relabel old work. Future timesheets capture stable resource ID and acting user separately. Retirement cannot delete links; large team history requires bounded as-of queries. Restrict backdated edits until correction/snapshot policy exists.

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
| AC-01 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-01: No-login create and identity-count/access checks. |
| AC-02 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-02: Valid/forged/duplicate link tests. |
| AC-03 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-03: Membership suspension and retirement preservation tests. |
| AC-04 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-04: Inclusive-start/exclusive-end date boundaries and invalid intervals. |
| AC-05 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-05: PostgreSQL overlap/concurrency tests. |
| AC-06 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-06: Archive-retire and historical query tests. |
| AC-07 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-07: Field projection, list/detail and forged ID tests. |
| AC-08 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-08: Version conflict, relink denial and event atomicity tests. |

## Definition of implementation readiness
Resolve D-022, relevant upstream contracts and D-024; finalize endpoint examples
and capability matrix. Owner authorizes implementation separately. Design remains a
review draft until then; all new model/API names may change during review.

## Date and retirement details for review
For this first slice use organization-local business dates: start_date must be today
or later; an existing interval may end today or later and strictly after start_date.
Changing an already-ended interval or moving its start backward is rejected pending
historical correction design. Unlink time is server UTC now, not caller-backdated.
Retirement rejects new team intervals but does not rewrite old intervals; active-team
lists explicitly distinguish retired resources until their intervals are ended.
Contact fields are not accepted by create/update in this slice; ResourceContact storage
may be deferred entirely until a dedicated contact-edit contract is approved. Do not
build an unreachable PII store merely because the model sketch names one.


2026-10-18 follow-up: [0009](../0009-resource-selection/design.md) adds direct member selection and automatic stable identity reuse. Manual duplicate Person creation is no longer required for existing members. Historical rules remain.
