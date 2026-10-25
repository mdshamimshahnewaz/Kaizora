# Tasks — 0004 Roles & Permissions

Status: Implemented — approved scope; verification and owner acceptance remain separate.
Date: 2026-10-18 · Constitution: 1.1 · Implementation authorised: Yes — owner: “0004 full approved”, 2026-10-18.
The owner approved this feature in full and requested implementation, followed by 0003 integration. Final implementation resolutions below govern over earlier proposal wording.

[Design](design.md) · [Acceptance](spec.md)

Implementation tasks completed; see verification.md for executed evidence and production limits.

- [x] **T-01 — Resolve decisions and freeze contracts.**
  - Depends on: D-019, D-024 and upstream features: 0003 scope and membership contracts. Implement its policy port without introducing organizations -> identity -> organizations imports.
  - Covers: AC-01–AC-08; design decisions/API.
  - Done when: owner choices and implementation authority are recorded; role/action
    matrix and serializer examples are concrete; no policy is silently inferred.
- [x] **T-02 — Add owned data, migrations and invariant tests.**
  - Depends on: T-01. Covers: AC-01–AC-08 data/permission/history cases.
  - Scope: backend/modules/identity/, backend/tests/.
  - Done when: additive PostgreSQL migrations and constraints preserve existing data;
    relevant failing invariant tests exist before changing behaviour.
- [x] **T-03 — Implement public use cases and DRF adapters.**
  - Depends on: T-02. Covers: AC-01–AC-08 backend portions.
  - Scope: owning module interfaces/services/API, config registration and generated schema.
  - Done when: authorization, historical rules, conflict/rollback and atomic events are
    enforced through the same commands from API and any Admin mutations; schema validates.
- [x] **T-04 — Add typed frontend slice.**
  - Depends on: T-03. Covers: AC-01–AC-08 applicable UI outcomes.
  - Scope: frontend/src/features/identity/, route/shell integration, generated types.
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
