# Timely V4 — Frontend API Client Rules

> **Authority:** Subordinate to `docs/constitution.md` (v1.1), `docs/architecture.md` and `docs/api-conventions.md`.
> **Status:** **PROPOSED** unless marked otherwise. Builds on the existing `frontend/lib/api/client.ts`.

## 1. Location and access
- One shared client lives in `frontend/lib/api/`. **PROPOSED**
- Components and pages never call `fetch` to Django directly and never hardcode the backend URL. **CONFIRMED direction (P8)**
- Feature-specific functions live in `frontend/lib/api/<feature>.ts` and return typed results. **PROPOSED**
- No file in `frontend/` imports a database driver or ORM, or holds database credentials. **CONFIRMED (P8)**

## 2. Server-side only
- The client is `server-only` (as today). Browser-side calls to Django are **OPEN** (see `docs/decisions.md`); until decided, the browser does not call Django directly.
- The base URL comes from the `API_URL` environment variable (as today). No backend secrets go in `NEXT_PUBLIC_*`. **PROPOSED**
- `API_URL` is validated: absolute HTTP(S) URL, no credentials, query or fragment (as today). **PROPOSED**

## 3. Request defaults
- Timeout on every request (5 s default, overridable per call with justification). **PROPOSED**
- `redirect: "error"`, `Accept: application/json`, and `cache: "no-store"` unless the feature plan justifies caching. **PROPOSED**
- Authentication and session are forwarded server-side. Constitution P5 applies (no tokens in browser storage; no tokens, secrets or personal data in logs). **PROPOSED**
- `request_id` from the backend is propagated into logs and error reports. **PROPOSED**

## 4. Responses and errors
- Non-2xx responses are mapped to `ApiClientError`, keeping the backend error envelope's `code`, `status`, `errors[]` and `request_id`. **PROPOSED**
- Responses are checked against the expected shape before use. Runtime schema validation with a library is **OPEN** (new dependency); until then, hand-written type guards are used (as in `getHealth`). **PROPOSED**
- UI mapping: 401 → sign-in, 403 → forbidden, 404 → not found, network/timeout/5xx → an "unavailable" state for that region. **PROPOSED**

## 5. Pagination and lists
- Shared helpers handle the pagination envelope (`docs/api-conventions.md` §3). Pages never request unbounded lists. **PROPOSED**

## 6. Testing
- The shared client has automated tests (as in `frontend/tests/api-client.test.mjs`): configuration errors, timeout, network failure, HTTP errors, invalid responses, and error-envelope mapping. **PROPOSED**
- Each feature function is tested against mocked Django responses. **PROPOSED**

## 7. Enforcement
Lint rules forbidding DB drivers and direct Django `fetch` outside `lib/api/` are wanted. The tooling is **OPEN** (new dependency or config needs approval, P7). Until then, reviewers check these rules and each `validation.md` records the check.

## 8. Next.js version
This Next.js version has breaking changes. Before writing Route Handlers, caching or other Next code, read the relevant guide in `frontend/node_modules/next/dist/docs/` (see `frontend/AGENTS.md`, which is tool-generated and must not be edited).
