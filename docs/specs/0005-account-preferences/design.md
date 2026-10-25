# Design — 0005 Account & Preferences

> Implementation update (2026-10-18): the owner authorized 0005–0008 in App UI and Django Admin. [Delivery decisions and evidence](../0005-0008-delivery.md) supersede the original draft-only labels below. Owner UI/UX acceptance is still pending.

Status: Implemented — owner UI/UX acceptance pending.
Date: 2026-10-18 · Constitution: 1.1 · Implementation authorised: Yes, by the owner on 2026-10-18.
Original planning detail is retained below; the delivery record documents adopted decisions, actual contracts and verification limits.

[Specification](spec.md) · [Tasks](tasks.md) · [Verification plan](verification.md)

## Ownership and dependencies
Owner: `identity`. 0002 session lifecycle; organization context from 0003 for effective preference fallback.

## Data model and constraints
Reuse identity.User first_name/last_name without replacing the user table. Add AccountPreferences(user one-to-one,theme nullable,timezone nullable,version) and a profile revision mechanism covering atomic name/preferences changes. Never add role or organization authority fields to a self-service serializer. Avoid storing duplicate display_name; derive using the existing convention.

## Public interfaces and transaction boundary
Proposed signatures describe contracts, not implemented functions. Scope DTOs carry
actor, organization and membership IDs; they are never a permanent permission grant.
get_account(actor_id) -> AccountDTO; update_account(actor_id, expected_version, profile_patch, preference_patch) -> AccountDTO. Identity owns the transaction. Organization timezone is resolved through organizations.interfaces for an explicitly selected accessible organization. Return own username/email as read-only; preferences contain no credentials.
Commands own atomic writes; downstream modules receive frozen DTOs only.

## API contracts
| Method | Path | Actor / permission | Request | Success / specific error |
| --- | --- | --- | --- | --- |
| GET | /api/v1/account/me/ | Active signed-in user | — | 200 {id,username,email,first_name,last_name,display_name,preferences,version} |
| PATCH | /api/v1/account/me/ | Same user + CSRF | {first_name?,last_name?,preferences?:{theme?,timezone?},version} | 200 account; 400 invalid/forbidden fields; 409 stale |

Response records expose stable IDs, permitted fields from the model section and version;
exclude private event records, secrets and fields without read permission. Timestamp
fields are ISO 8601 with offset. Define final serializer examples once owner decisions
are resolved; these draft contracts must not be treated as generated OpenAPI.

## Frontend behaviour
Extend existing /app/account with Profile and Preferences sections, labelled forms and save feedback. Preserve read-only username/email. Use existing shadcn controls; server preferences integrate with ThemeProvider without a second independent theme store. Session snapshot retains its existing contract; account detail is fetched separately. Account remains accessible with no organization membership.
Use typed feature API wrappers, not component-level ad-hoc fetch. Loading, empty,
validation, conflict, denied and unavailable states must be separately reviewable.

## Alternatives and decisions
D-020: confirm self-editable fields and whether preferences should follow the user across devices. Recommended first/last name + theme/timezone only. Username/email changes, password change/reset and session-management screens require a separate security feature. Localization/date-format selection is deferred; do not create a language dropdown with no translated UI.

## Feature risks
Duplicated local/server preferences can cause flicker and stale overwrites. Specify precedence and version checks before code. Existing Django Admin profile edits must advance the same version or use the same update use case.

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
| AC-01 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-01: Self endpoint and attempted user_id override tests. |
| AC-02 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-02: Allowed field update and forbidden mass-assignment tests. |
| AC-03 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-03: IANA timezone and enum validation; atomic failure. |
| AC-04 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-04: Two-tab edits and conflict recovery. |
| AC-05 | Frontend behaviour and API contracts | T-03, T-04, T-05 | V-05: Two-org fallback tests and timestamps at date boundaries. |
| AC-06 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-06: Presentation-only regression with fixed source records. |
| AC-07 | Data constraints, public interfaces and API contracts | T-02, T-03, T-05 | V-07: Anonymous and CSRF endpoint tests. |
| AC-08 | Frontend behaviour and API contracts | T-03, T-04, T-05 | V-08: Shared provider refresh and retry UI tests. |

## Definition of implementation readiness
Resolve D-020, relevant upstream contracts and D-024; finalize endpoint examples
and capability matrix. Owner authorizes implementation separately. Design remains a
review draft until then; all new model/API names may change during review.
