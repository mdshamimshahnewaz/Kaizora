# Tasks — 0006 Clients & Contacts

> Implementation update (2026-10-18): the owner authorized 0005–0008 in App UI and Django Admin. [Delivery decisions and evidence](../0005-0008-delivery.md) supersede the original draft-only labels below. Owner UI/UX acceptance is still pending.

Status: Implemented — owner UI/UX acceptance pending.
Date: 2026-10-18 · Constitution: 1.1 · Implementation authorised: Yes, by the owner on 2026-10-18.
Original planning detail is retained below; the delivery record documents adopted decisions, actual contracts and verification limits.

[Design](design.md) · [Acceptance](spec.md)

Implementation tasks are completed with executed evidence and remaining verification limits in verification.md and the shared delivery record. Owner acceptance is a separate step.

- [x] **T-01 — Resolve decisions and freeze contracts.**
  - Depends on: D-021, D-024 and upstream features: 0003 organization scope, 0004 clients permissions. Projects will consume client summary DTOs in 0008.
  - Covers: AC-01–AC-08; design decisions/API.
  - Done when: owner choices and implementation authority are recorded; role/action
    matrix and serializer examples are concrete; no policy is silently inferred.
- [x] **T-02 — Add owned data, migrations and invariant tests.**
  - Depends on: T-01. Covers: AC-01–AC-08 data/permission/history cases.
  - Scope: backend/modules/clients/, backend/tests/.
  - Done when: additive PostgreSQL migrations and constraints preserve existing data;
    relevant failing invariant tests exist before changing behaviour.
- [x] **T-03 — Implement public use cases and DRF adapters.**
  - Depends on: T-02. Covers: AC-01–AC-08 backend portions.
  - Scope: owning module interfaces/services/API, config registration and generated schema.
  - Done when: authorization, historical rules, conflict/rollback and atomic events are
    enforced through the same commands from API and any Admin mutations; schema validates.
- [x] **T-04 — Add typed frontend slice.**
  - Depends on: T-03. Covers: AC-01–AC-08 applicable UI outcomes.
  - Scope: frontend/src/features/clients/, route/shell integration, generated types.
  - Done when: actual API data, scoped requests and all documented UI states work with
    existing components; relevant interaction tests pass without fabricated records.
- [x] **T-05 — Verify and record outcomes.**
  - Depends on: T-02–T-04. Covers: AC-01–AC-08, V-01–V-08.
  - Done when: verification.md records executed environment/commands/evidence per AC;
    PostgreSQL, auth regressions, module boundaries, typecheck/lint/build and applicable
    browser checks are recorded; remaining gaps are explicit and feature index updated.

## Implementation stopping condition
Do not start T-02 while an upstream contract or required policy is unresolved. Split
tasks further during approved implementation planning if the slice exceeds a reviewable
change. No deployment, bulk data import or server startup is authorised by this file.
