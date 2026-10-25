# Timely V4 — Architecture Rules

> **Authority:** Subordinate to `docs/constitution.md` (v1.1). Where this document conflicts with the Constitution, the Constitution wins and the conflict must be raised, not resolved silently.
> **Status labels:** CONFIRMED, PROPOSED, OPEN, DEFERRED (see the Constitution). Rules below are **PROPOSED** unless marked otherwise. Only the project owner can promote them.
> **Precedence:** Constitution → `docs/` rules → feature spec/plan. A feature that deviates from a rule needs an explicit, owner-approved exception recorded in its `plan.md`.

## 1. System shape
- One deployable Django application (modular monolith) plus a Next.js frontend, backed by PostgreSQL. **[CONFIRMED: P3, P8]**
- Next.js is the presentation layer. Django REST Framework is the authoritative application API and business-logic layer. **[CONFIRMED: P8]**

## 2. Rules

| ID | Rule | Status |
|---|---|---|
| AR-1 | Business logic, validation, authorisation and data access live only in Django. Next.js contains presentation logic only. | CONFIRMED (P8) |
| AR-2 | The frontend never connects to PostgreSQL: no DB driver, no ORM, no DB credentials in frontend code or environment. | CONFIRMED (P8) |
| AR-3 | Every frontend business operation and data read goes through the approved Django API, using the shared API client (`docs/frontend-api-client.md`). | CONFIRMED (P8) |
| AR-4 | Next.js Route Handlers / BFF are allowed only for explicitly justified frontend-specific needs (see §3). They never replace Django business APIs. | CONFIRMED (P8), detail PROPOSED |
| AR-5 | Django modules communicate through defined internal interfaces. A module never imports another module's models, tables or internals. Not every operation needs an HTTP endpoint. | CONFIRMED direction (P3, P8), detail PROPOSED |
| AR-6 | The API layer is thin: views/serializers handle HTTP and input validation; a service layer holds use cases and invariants. Further layers are added only where complexity justifies them. No empty layers or speculative abstractions. | PROPOSED (P3) |
| AR-7 | External systems (ORBIS, UNIS, Microsoft Entra/Graph, AI providers) are accessed only through backend adapters (Constitution P4). The frontend never calls them. | CONFIRMED (P4, P8) |
| AR-8 | Each entity/table has exactly one owning module. Other modules reach its data only through the owner's internal interface. | PROPOSED |
| AR-9 | Security (server-side authorisation, secrets, diagnostics, auditability) is governed by Constitution P5 and is not restated here. Each feature's plan specifies authorisation per endpoint (`docs/api-conventions.md` §6). | CONFIRMED (P5) |
| AR-10 | No new dependency, tool or infrastructure is added without owner approval (P7). Rules that need tooling to be enforced (import boundaries, lint rules, OpenAPI generation) stay documented rules until that tooling is approved. | CONFIRMED (P7) |
| AR-11 | **Dependency direction and cycle prevention.** Each feature plan declares the modules it depends on. Dependencies are one-directional and must not be circular. When a mutual dependency arises, the plan proposes interface inversion or a third module and requests an owner decision. | PROPOSED (P3) |
| AR-12 | **Internal module communication.** Modules communicate in-process through the owning module's public interface by default. Internal HTTP calls between modules require an explicitly approved requirement. | PROPOSED (P3, P8) |
| AR-13 | **Transaction boundaries.** Each transaction has one clearly identified owning module/service. Cross-module use cases coordinate through public interfaces. Distributed transactions and the outbox pattern remain OPEN unless separately decided. | PROPOSED (P3) |
| AR-14 | **Client API parity.** Web and future mobile clients consume the documented Django REST Framework APIs. Client-specific presentation must not create duplicate business APIs. | PROPOSED (P8) |

## 3. Next.js Route Handlers / BFF
**Allowed, with a written justification in the feature's `plan.md` and an entry in the register below:**
- Session/cookie handling and token forwarding or refresh (e.g. HttpOnly cookies; tokens are never in browser storage, P5).
- Relaying streams (SSE) or uploads where the browser cannot call Django directly.
- Frontend-only aggregation of several Django API calls for rendering, containing no business rules.

**Not allowed:**
- Business rules, authorisation decisions or validation that is the source of truth.
- Direct database access.
- Calling external systems (ORBIS, UNIS, Entra/Graph, AI) directly.
- Replacing or duplicating a Django business endpoint.

**BFF register** (one row per Route Handler; empty until the first is approved):

| Handler | Feature | Justification | Approved by / date |
|---|---|---|---|
| `GET /auth/login` | 002-authentication | Browser redirect to Entra and a short-lived HttpOnly binding cookie on the Next.js origin. Calls Django `login/start/`. | Project owner, 2026-10-11 (plan approval) |
| `GET /api/auth/callback/azure-ad` | 002-authentication | Entra redirects the browser to the Next.js origin at the registered URI; sets the HttpOnly session cookie (cookie handling, P5). Calls Django `login/complete/`. Path defined once in `lib/auth/paths.ts`. | Project owner, 2026-10-11 (plan approval); path amended 2026-10-13 (amendment A-1) |
| `POST /auth/logout` | 002-authentication | Same-origin check, calls Django `logout/`, clears the session cookie. | Project owner, 2026-10-11 (plan approval) |
| `GET /brand/logo` | 003-about-page | Relays the logo image bytes from Django; the browser may not call Django (D-56), so an image `src` needs a same-origin URL. Public (needed before sign-in). Must not hold business rules, auth decisions or serve other content types. | Project owner, 2026-10-13 (plan approval) |
| `GET /brand/favicon` | 003-about-page | Same relay for the favicon. | Project owner, 2026-10-13 (plan approval) |

`proxy.ts` is an optimistic cookie-presence redirect, not a Route Handler and not a security boundary (pages call `requireUser()`; Django authenticates every API call).

## 4. Backend module guidance
- The module list, folder structure and boundary enforcement are **OPEN** (Constitution P3). The first feature plan that needs a module proposes them for approval. `attendance` (spec 004, D-61) is the first clean-architecture module: other code imports only `attendance.public`, and `attendance/tests/test_boundary.py` enforces it. Its Django Admin pages (schedule, sync, backfill jobs, reconciliation, health, audit; A-1, D-64) are part of the module and are not an API.
- Until approved, no new module structure is assumed. The existing `core` app stays as the foundation (P1).
- Modules expose an internal interface (a small, documented set of service functions or classes). Cross-module calls use only that interface.
- Cross-module database foreign keys and joins are **OPEN**; each feature plan states how it references another module's data.

## 5. Requirements on every feature
Every `specs/<feature>/` must address, in the specified document:

| Topic | Spec | Plan |
|---|---|---|
| API contracts | Operations clients need; permission cases as acceptance criteria | Full per-endpoint contract (`docs/api-conventions.md`) |
| Data ownership | Business-level owner and sensitivity of the data | Owning module, tables/entities, internal interfaces used, and cross-module data access (AR-8) |
| Module ownership and dependencies | — | Owning module/domain; each dependency on another module with its reason (AR-11); public interfaces used or introduced (AR-5, AR-12) |
| Transactions and consistency | — | Transaction boundaries and owning module/service; consistency considerations across modules (AR-13) |
| Security | Who may do what; sensitive data; auditable events | AuthN/AuthZ design, validation, secrets, audit |
| External systems | Which systems are involved | Adapters used; failure behaviour |
| BFF | — | Justification or "None" |
| Testing | Testable acceptance criteria | Strategy by layer (service, API, frontend client) |

## 6. Known foundation gaps (pre-existing, not changed by this document)
These predate the Constitution (P1). Each needs its own approved spec before change.
- ~~`backend/config/settings.py` hardcodes `SECRET_KEY` and sets `DEBUG = True`~~ Fixed by spec 002 (environment-based; validation pending).
- ~~`GET /api/system-info` is unauthenticated~~ Fixed by spec 002 (superuser-only; validation pending).
- DRF authentication, default permission and exception handling are configured by spec 002. Pagination is still not configured.
