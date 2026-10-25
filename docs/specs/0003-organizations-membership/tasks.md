# Tasks — 0003 Organizations & Membership

Status: Implementation tasks completed within 0003; see verification limits.
Date: 2026-10-18 · Constitution: 1.1 · Implementation authorised: Yes — “Please implement”, 2026-10-18.
All new product choices and API/data shapes below are PROPOSED unless inherited from the constitution.

[Design](design.md) · [Acceptance](spec.md)

Tasks executed for the 0003 slice. Manager-policy integration and management UI are now complete through approved 0004.

- [x] **T-01 — Resolve decisions and freeze contracts.**
  - Depends on: D-018 (product direction approved), D-024 and upstream features: Existing 0002 authentication; 0004 is required before general membership-management UI is enabled.
  - Covers: AC-01–AC-08; design decisions/API.
  - Done when: owner choices and implementation authority are recorded; role/action
    matrix and serializer examples are concrete; no policy is silently inferred.
- [x] **T-02 — Add owned data, migrations and invariant tests.**
  - Depends on: T-01. Covers: AC-01–AC-08 data/permission/history cases.
  - Scope: backend/modules/organizations/, backend/tests/.
  - Done when: additive PostgreSQL migrations and constraints preserve existing data;
    relevant failing invariant tests exist before changing behaviour.
- [x] **T-03 — Implement public use cases and DRF adapters.**
  - Depends on: T-02. Covers: AC-01–AC-08 backend portions.
  - Scope: owning module interfaces/services/API, config registration and generated schema.
  - Done when: authorization, historical rules, conflict/rollback and atomic events are
    enforced through the same commands from API and any Admin mutations; schema validates.
- [x] **T-04 — Add typed frontend slice.**
  - Depends on: T-03. Covers: AC-01–AC-08 applicable UI outcomes.
  - Scope: frontend/src/features/organizations/, route/shell integration, generated types.
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

## Execution note
T-01 technical resolutions are recorded in design.md; product scope is unchanged.
T-05 covers executed automated checks and desktop empty-state inspection. Full browser
mutation flow, mobile/theme-specific visual checks and load benchmark were not executed.
No commit was created because this workspace has no functioning Git repository.
