# Design — NNNN feature

Status: Draft · Spec: `spec.md` (in the destination feature folder) · Owner approval: Not recorded

## Architecture and ownership
Owning modules, dependencies/direction, orchestration and transaction owners.

## Data and migrations
Entities, constraints/indexes, effective periods, historical snapshots/corrections,
custom-field types/querying, data migration/backfill, rollback and compatibility.

## Internal interfaces
Commands/queries, typed immutable DTOs, errors, actor/tenant scope, permissions and
transaction boundary. No model/QuerySet return across modules.

## HTTP contract
For each endpoint: method/path, authentication/permission, request/response examples,
status/error shapes, pagination/limits/filter/sort, concurrency/idempotency. Specify
OpenAPI/type generation impact and compatibility with existing web/future mobile.

## Security and external adapters
Access denial, audit/redaction/retention, secrets, CSRF, external timeout/retry and
failure recovery. Mark N/A with reasons; unresolved choices link decision IDs.

## Frontend
Routes, shared client wrappers, reusable components, loading/empty/error/permission
states, accessibility, mobile layout and light/dark behaviour. React/Vite conventions.

## Alternatives and decisions
| Choice | Rationale/tradeoff | Status / decision ID |
| --- | --- | --- |

## Traceability and validation plan
| AC | Design section | Task | Planned test/manual check |
| --- | --- | --- | --- |

## Risks and constitution compliance
Map applicable P1–P9 principles to design evidence; explain deviations and blockers.
Include workload assumptions, migration/deployment risks and rollback limits.

## Change log
| Date | Change | Reason | User direction / approval |
| --- | --- | --- | --- |
