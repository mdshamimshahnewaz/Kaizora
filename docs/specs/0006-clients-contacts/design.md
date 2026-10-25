# Design — 0006 Clients & Contacts

> Implementation update (2026-10-18): the owner authorized 0005–0008 in App UI and Django Admin. [Delivery decisions and evidence](../0005-0008-delivery.md) supersede the original draft-only labels below. Owner UI/UX acceptance is still pending.

Status: Implemented — owner UI/UX acceptance pending.
Date: 2026-10-18 · Constitution: 1.1 · Implementation authorised: Yes, by the owner on 2026-10-18.
Original planning detail is retained below; the delivery record documents adopted decisions, actual contracts and verification limits.

[Specification](spec.md) · [Tasks](tasks.md) · [Verification plan](verification.md)

## Ownership and dependencies
Owner: `clients`. 0003 organization scope, 0004 clients permissions. Projects will consume client summary DTOs in 0008.

## Data model and constraints
Client(id UUID,organization_id,code,normalized_code,name,status,version,created_at); Contact(id UUID,organization_id,client_id,name,email,phone,position,status,version); ClientChangeEvent/ContactChangeEvent with redacted change metadata. Unique (organization_id,normalized_code). Index organization/status/name/id. Contact sensitivity and retention require a policy; omit home address and unrelated personal details.

## Public interfaces and transaction boundary
Proposed signatures describe contracts, not implemented functions. Scope DTOs carry
actor, organization and membership IDs; they are never a permanent permission grant.
get_client_summary(scope, client_id, require_active=False) -> ClientSummaryDTO; lock_active_client(scope, client_id) -> ClientSummaryDTO (requires caller-owned transaction, locks only the client row, no writes); list_clients(scope, query) -> PageDTO; create_client(scope, command) -> ClientDTO; update_client(scope, command) -> ClientDTO; change_contact(scope, client_id, command) -> ContactDTO. Clients owns writes and permission checks through identity.interfaces; never accept an organization inferred solely from a contact ID.
Commands own atomic writes; downstream modules receive frozen DTOs only.

## API contracts
| Method | Path | Actor / permission | Request | Success / specific error |
| --- | --- | --- | --- | --- |
| GET | /api/v1/organizations/{org}/clients/ | clients.read | page,search,status,ordering | 200 paginated summaries |
| POST | /api/v1/organizations/{org}/clients/ | clients.manage | {code,name} | 201 client; 409 duplicate |
| GET | /api/v1/organizations/{org}/clients/{id}/ | clients.read | — | 200 client; 404 inaccessible/missing |
| PATCH | /api/v1/organizations/{org}/clients/{id}/ | clients.manage | {name?,status?,version,reason} | 200 client; 409 stale |
| GET | /api/v1/organizations/{org}/clients/{id}/contacts/ | contacts.read | page,status | 200 paginated contacts |
| POST | /api/v1/organizations/{org}/clients/{id}/contacts/ | contacts.manage | {name,email?,phone?,position?} | 201 contact |
| PATCH | /api/v1/organizations/{org}/clients/{id}/contacts/{contact}/ | contacts.manage | {name?,email?,phone?,position?,status?,version,reason} | 200 contact; 409 stale |

Response records expose stable IDs, permitted fields from the model section and version;
exclude private event records, secrets and fields without read permission. Timestamp
fields are ISO 8601 with offset. Define final serializer examples once owner decisions
are resolved; these draft contracts must not be treated as generated OpenAPI.

## Frontend behaviour
Client list/detail/contact tabs at /app/o/:orgId/clients. Server-side search and archive filter; explicit permission empty state. Contact PII is omitted, not merely hidden, when contacts.read is absent. Archive confirmation describes preserved references. No projects tab full of invented data before 0008.
Use typed feature API wrappers, not component-level ad-hoc fetch. Loading, empty,
validation, conflict, denied and unavailable states must be separately reviewable.

## Alternatives and decisions
D-021: confirm client code policy and contact visibility. Recommended human-assigned unique code within organization, name not unique, separate contact read/manage capabilities. Code immutable in first version; correction flow later if needed. No payment/billing detail collected yet.

## Feature risks
Archive state can race with project creation. 0008 must validate and lock referenced client state inside its transaction using a clients public interface; archive does not require a projects callback. PII redaction/retention needs explicit deployment policy.

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
| AC-01 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-01: Create/read and cross-tenant detail/list tests. |
| AC-02 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-02: Case-normalized code uniqueness and concurrent create tests. |
| AC-03 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-03: Forged client/contact nesting and field validation tests. |
| AC-04 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-04: Archive preservation plus 0008 contract test fixture. |
| AC-05 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-05: Search/filter/page limits, stable ordering and tenant-filter tests. |
| AC-06 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-06: Optimistic concurrency and redaction tests. |
| AC-07 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-07: Interface/static-boundary checks and DTO immutability. |
| AC-08 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-08: Rename/link preservation and explicit snapshot-boundary review. |

## Definition of implementation readiness
Resolve D-021, relevant upstream contracts and D-024; finalize endpoint examples
and capability matrix. Owner authorizes implementation separately. Design remains a
review draft until then; all new model/API names may change during review.
