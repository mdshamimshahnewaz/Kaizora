# 0001: Development foundation

Status: implemented; see verification.md for actual checks and limitations.

## Goal
Create a runnable backend/frontend foundation in this directory for an API-first,
specification-driven modular monolith. Preserve existing `rebuild/` references.
SDD is interpreted as Specification-Driven Development.

## Scope
- Django Admin, DRF, PostgreSQL configuration and custom User before migrations.
- `/api/v1/health/live/` and `/api/v1/health/ready/` with explicit response contracts.
- OpenAPI export, generated React API types and a live connection screen.
- Domain ownership document, reserved packages and a static import-boundary check.
- Local setup/run/check instructions and dependency lockfiles.

## Acceptance criteria
- F1: PostgreSQL starts locally and Django migrations apply.
- F2: Anonymous liveness returns 200 and `{status: ok, service: kaizora-api, api_version: v1}`.
- F3: Readiness queries PostgreSQL; database failure returns sanitized 503.
- F4: Custom user supports Django Admin authentication; private API defaults to authenticated.
- F5: OpenAPI validates and generates TypeScript used by the React API client.
- F6: React builds and shows real API connection success or failure without fake business data.
- F7: Ordinary cross-module imports are permitted only through interfaces.py; violations fail checks.
- F8: SDD templates, module ownership and historical invariants are documented.

## Non-goals
Business CRUD, tenant schema, end-user login, mobile app/authentication, replacement
logic, billing engine, legacy migration, production deployment and microservices.
No business capability is implied by a reserved module directory.

## Verification strategy
Scaffold/configuration uses smoke verification, not test-first implementation.
Behavior checks cover health success/failure and a real PostgreSQL/Admin path.
Boundary checker includes positive/negative examples. Build and browser checks
cover frontend integration. Record blocked checks rather than substitute SQLite.
