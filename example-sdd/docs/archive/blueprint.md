# TimeLy Architecture Blueprint

Status: Draft v1. Modular monolith (DRF + Next.js + PostgreSQL), microservice-ready, spec-driven.

## 1. Goals and honest trade-offs

| Goal | How | Caveat |
| --- | --- | --- |
| A failed domain never breaks others | Fault isolation at module boundaries (timeouts, circuit breakers, UI error boundaries) | In one process, a crash, memory leak or infinite loop still takes everything down. Isolation is logical, not physical. Real isolation needs separate processes (Phase 3). |
| Move to microservices later | Strict boundaries: no cross-domain imports, no cross-domain FKs or joins, contracts only | Needs discipline enforced by tooling, not convention. |
| Clean architecture | Dependency rule: domain <- application <- infrastructure/interfaces | Django ORM models are infrastructure, not domain. Keep them separate from domain entities. |
| Spec-driven, agent-manageable | `specs/` is the source of truth; agents read specs, then implement, then verify | Specs must be small, testable and kept current. |

## 2. What is needed to set up (gap list vs. current repo)

Current: Django 6.1 + DRF + django-environ + psycopg, one `core` app, health endpoint; Next 16 frontend with a health client; one root `plan.md`.

Must do:
1. **Secrets**: `SECRET_KEY` is hardcoded in `backend/config/settings.py`. Move to env, set `DEBUG` from env. Blocking before any commit of settings.
2. **Split settings**: `config/settings/{base,local,production,test}.py`.
3. **Python tooling**: `pyproject.toml`, ruff (lint+format), mypy/pyright, pytest + pytest-django, `import-linter` (enforces boundaries), split requirements (`base/dev`) or use uv. Remove `psutil`/`Markdown` if unused.
4. **API contract**: `drf-spectacular` (OpenAPI per domain) and generate frontend TypeScript types from it (`openapi-typescript`).
5. **Local infra**: no Docker; use the locally installed PostgreSQL. Add backend `.env.example`, a `scripts/` folder (PowerShell) or `justfile` with `setup`, `test`, `lint`, `dev`, and a documented DB bootstrap (create role/db, `CREATE SCHEMA` per module).
6. **Frontend tooling**: Vitest/Playwright, `eslint-plugin-boundaries` (or dependency-cruiser) for module boundaries, Prettier.
7. **CI** (GitHub Actions): lint, typecheck, boundary check, tests, contract drift check, build.
8. **Spec artifacts**: `specs/`, `AGENTS.md`, ADRs (below).
9. **Decisions**: see section 10 (auth, jobs, real-time, integrations, hosting).

Defer (do not add yet): Docker/Kubernetes, message broker, API gateway, service mesh.

## 3. Backend layout (Django modular monolith)

```
backend/
  config/                  # settings, root urls, asgi/wsgi (composition root only)
  platform/                # shared kernel: base errors, result types, event bus iface, clock, ids (NO business logic)
  modules/
    <domain>/              # e.g. identity, tracking, projects, reporting
      domain/              # entities, value objects, domain events, repository INTERFACES (pure Python, no Django/DRF)
      application/         # use cases / commands / queries, DTOs, ports (interfaces to other modules)
      infrastructure/      # Django models, migrations, repository impls, adapters to other modules
      interfaces/          # DRF views, serializers, urls, admin   (thin, call use cases only)
      public_api.py        # the ONLY importable surface for other modules (facade + event contracts)
      tests/
      module.md            # owner, purpose, contracts, events, dependencies
```

Rules (enforced by import-linter in CI):
- `domain` imports nothing from Django, DRF, or other modules.
- `application` imports `domain` and ports only.
- `interfaces` and `infrastructure` depend inward, never the reverse.
- Module A may import only `modules.B.public_api`; never B's models/internals.
- **Data isolation**: each module owns its tables (prefix `<module>_` or its own PG schema). No cross-module FK constraints or joins; store foreign IDs as plain UUIDs and resolve via `public_api`/read models. Optionally one DB role per schema.
- **Cross-module communication**: (a) synchronous call via port -> adapter -> `public_api`, wrapped with timeout + circuit breaker + fallback; (b) asynchronous domain events via an outbox table (transactional outbox) and in-process dispatcher first, broker later.
- **Failure isolation**: URLs mounted per module under `/api/v1/<module>/`; a module-level exception middleware returns a scoped 503 problem+json; module registry (`MODULES` setting) lets a module be disabled via feature flag without touching others; health endpoint per module (`/api/v1/<module>/health`) plus aggregate.
- Use UUID primary keys (microservice-safe), idempotency keys on commands, and versioned event schemas.

## 4. Frontend layout (Next.js App Router)

```
frontend/
  app/                     # routing/composition only; each domain route group is independent
    (identity)/ (tracking)/ ...
  modules/<domain>/
    api/                   # generated client + typed fetchers for that domain only
    domain/ (types, mappers), components/, hooks/, actions/ (server actions), index.ts (public surface)
  shared/                  # design system, http client (timeout, retry, error mapping), utils (no domain logic)
  lib/api/client.ts        # existing; becomes shared/http
```

Rules:
- Modules import only `shared` and other modules' `index.ts`; prefer none.
- Every domain route segment has its own `error.tsx`, `loading.tsx` and Suspense boundary, so one failing backend domain renders an "unavailable" panel only for that region.
- Server-only per-domain base URL env vars (`TRACKING_API_URL`, ...) defaulting to one gateway URL; this makes the later split a config change.
- Dashboard-style pages compose domain widgets with independent Suspense + error boundaries (parallel fetch, partial failure allowed).

## 5. Microservice-readiness roadmap

1. **Phase 1 (now)**: monolith, enforced boundaries, per-domain tables, outbox events, generated contracts.
2. **Phase 2**: per-domain DB schema + DB roles; run the same image with `ENABLED_MODULES=tracking` (multiple deployments, one codebase); reverse proxy routes `/api/v1/<module>` to each.
3. **Phase 3**: extract a module into its own repo/service: its `public_api` becomes HTTP/gRPC client adapter implementing the same port; in-process event bus swapped for a broker. Consumers change only the adapter.

Extraction test per module: "Can I delete every other module and still run its tests?" must be true.

## 6. Spec-driven workflow (agent-friendly)

```
AGENTS.md                      # how agents work here: read order, commands, rules, definition of done
specs/
  constitution.md              # non-negotiable principles (sections 1, 3, 4 rules)
  blueprint.md                 # this file
  adr/NNNN-title.md            # decisions (auth, events, db isolation, hosting)
  <domain>/
    spec.md                    # user stories, requirements (EARS: "When X, the system shall Y"), acceptance criteria
    plan.md                    # design: entities, use cases, API, events, failure modes
    tasks.md                   # small checklist tasks, each referencing requirement IDs
    contracts/                 # openapi.yaml, event schemas (JSON Schema)
```

Loop per feature: **spec -> clarify -> plan -> tasks -> implement (tests first) -> verify -> update spec**.
Definition of done: acceptance criteria covered by tests, boundary linter green, contract drift check green, spec updated.
Agent rules: one domain per task; never edit another module's internals; contract changes require spec + contract update first.

## 7. Quality gates (CI)

`ruff`, `mypy`, `import-linter`, `pytest` (unit tests need no DB for domain/application), integration tests on PostgreSQL, OpenAPI diff, `eslint` + boundaries, `tsc`, Vitest, Playwright smoke, build.

## 8. Suggested first milestones

1. M0 Hygiene: env-based secret, settings split, tooling, docker-compose, CI, `AGENTS.md`, `constitution.md`.
2. M1 Platform skeleton: module registry, error/problem format, per-module health, outbox, boundary lint rules; frontend `shared/http` and module error boundaries.
3. M2 `identity` domain (after auth ADR).
4. M3 First business domain end-to-end (e.g. `tracking`) as the reference implementation for agents to copy.
5. M4 Second domain + one cross-domain interaction (event + port) proving isolation by killing/disabling a module in tests.

## 9. Open questions

- Which SSO provider(s)? (Microsoft Entra ID, Google, ORBIS itself, other OIDC/SAML)
- How is ORBIS accessed: REST API, DB view, or file export? Does it offer webhooks/changed-since filters?
- How is UNIS reachable from the dev machine and from the future VPS (same LAN, VPN, public IP)? Can we get a read-only SQL login and the table/column docs?
- Which real-time features exactly (live punch feed, dashboards, notifications)?
- Scale: employee count, punches/day, number of devices/sites, time zones, shift rules.

## 10. Decisions (record as ADRs)

### ADR-0001 Domains (initial)
| Domain | Responsibility | Owns | Depends on |
| --- | --- | --- | --- |
| `identity` | SSO login, JWT, roles/permissions, user<->employee link | users, social accounts, roles | none |
| `employees` | Employee read model synced from ORBIS (ORBIS stays source of truth) | employee, org unit snapshots, sync cursor | none (ORBIS via adapter) |
| `attendance` | Punch ingestion from UNIS, normalised attendance records, later shifts/rules/reports | punches, daily attendance, sync cursor | `employees.public_api` (by employee ID only) |
| `realtime` / `notifications` (later) | Push events to clients | channels, subscriptions | consumes events only |

`identity` is built now; `employees` and `attendance` next. Keep `core` only for platform health until replaced by `platform/`.

### ADR-0002 Auth: SSO with django-allauth + JWT
- allauth handles the SSO handshake; on success the backend issues short-lived access JWT (djangorestframework-simplejwt) plus rotating refresh token in an HttpOnly, Secure, SameSite cookie. Browser JS never stores tokens.
- Next.js server (route handlers / server actions) holds the session and calls DRF with the access token; use the server-only API URL already in place.
- JWT claims: `sub` (user UUID), roles, `iat/exp`, `iss/aud`. No employee data in tokens; other modules authorise using `sub` plus roles. This keeps tokens verifiable by any future service (prefer asymmetric RS256/EdDSA keys so extracted services need only the public key).
- Link a user to an employee through a mapping (email or employee code) owned by `identity`, resolved via `employees.public_api`; never a DB foreign key.
- Restrict sign-in to allowed domains/tenants; no open self-registration; deny by default roles.

### ADR-0003 Integrations as anti-corruption layers
- ORBIS and UNIS are external systems. Each module has `infrastructure/adapters/<system>.py` that maps foreign models to our domain types. Foreign schemas never leak into `domain` or `application`.
- **UNIS (MSSQL)**: read-only SQL login; do not register it as a Django ORM database. Use a small adapter (`pyodbc` or `mssql-python`; requires Microsoft ODBC Driver for SQL Server on dev and VPS) behind a `PunchSource` port. Query incrementally by watermark (last punch id/timestamp + small overlap window), idempotent upsert keyed by (device, user code, timestamp). Handle UNIS time zone explicitly; store UTC. Keep raw punches separate from derived attendance so rules can be recomputed.
- **ORBIS**: behind an `EmployeeSource` port; scheduled incremental sync into `employees` tables; soft-delete/inactive handling; sync runs recorded (start, end, counts, errors).
- Failure behaviour: if UNIS or ORBIS is down, the sync job fails and retries with backoff; the app keeps serving last-synced data and shows a "data as of <time>" indicator. Nothing else breaks.
- Secrets for both live in env/secret store, never in the repo.

### ADR-0004 Background jobs and real-time (proposed, PostgreSQL-first)
Because PostgreSQL is already installed and Docker is not used, prefer fewer moving parts:
- **Jobs**: Procrastinate (PostgreSQL-native queue, Django integration, periodic tasks, retries). Jobs are thin wrappers that call application use cases; they live in each module's `interfaces/jobs.py`.
- **Real-time**: Server-Sent Events (SSE) for one-way live updates (punch feed, sync status) is simplest and works with Next.js; use Django Channels (ASGI, Daphne/Uvicorn) with `channels_postgres` only if two-way WebSockets are required. Events originate from the domain-event outbox.
- Alternative: Celery + Redis. More mature and widely known, but Redis is not available natively on Windows (needs Memurai/WSL) and adds an extra service on the VPS. Choose it only if throughput or team familiarity demands it. Because jobs call use cases, switching is low-cost.
- All jobs must be idempotent, have timeouts, and record status; per-module queues so a stuck domain cannot starve others.

### ADR-0005 Environments and hosting
- Dev: Windows, local PostgreSQL, Python venv, Node. Prod: Linux VPS, later decided. Plan for: Nginx or Caddy reverse proxy with TLS, Gunicorn+Uvicorn workers (ASGI for SSE/WebSockets), systemd units (web, frontend, worker), PostgreSQL backups, firewall/VPN path to UNIS and ORBIS. Cross-platform concerns: ODBC driver install, line endings, paths, time zones.
- Production hardening is a milestone after the first domains (DEBUG off, secure cookies, HSTS, ALLOWED_HOSTS, CORS/CSRF origins, structured logging, Sentry-style error tracking).

## 11. Updated milestones

1. M0 Hygiene (as above, without Docker): env secret, settings split, tooling, local DB bootstrap script, CI, `AGENTS.md`, `constitution.md`, ADRs 0001-0005 accepted.
2. M1 Platform skeleton: module registry, problem+json errors, per-module health, outbox, job runner, SSE endpoint; frontend `shared/http` and error boundaries.
3. M2 `identity`: allauth SSO, JWT issuance/refresh, roles, Next.js session handling. Spec first (`specs/identity/`).
4. M3 `employees`: ORBIS adapter + sync job + read API.
5. M4 `attendance`: UNIS adapter + incremental ingestion + live punch feed (SSE) + daily attendance computation.
6. M5 Isolation proof: tests that disable/fail one module or external source and show others keep working.
