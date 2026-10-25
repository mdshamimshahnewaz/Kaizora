# Timely V4 — API Conventions

> **Authority:** Subordinate to `docs/constitution.md` (v1.1) and `docs/architecture.md`.
> **Status:** all conventions are **PROPOSED** unless marked otherwise, pending project-owner review. Where a decision is not yet made it is marked **OPEN** and recorded in `docs/decisions.md`. A feature plan may rely only on PROPOSED/CONFIRMED items and must flag any OPEN item it depends on.

## 1. URLs and versioning
- Base path: `/api/v1/<module>/<resource>/`. Major version in the path. **PROPOSED**
- Plural, lower-case, kebab-case nouns for resources. Non-CRUD actions use `POST /<resource>/<id>/<verb>/`. **PROPOSED**
- The existing `GET /api/health/` stays as is until a feature changes it. **PROPOSED**
- A breaking change needs a spec update and a new version. **PROPOSED**

## 2. Representation
- JSON only. Field names are `snake_case` (DRF default). **PROPOSED**
- Date-times are ISO 8601 with offset, stored and returned in UTC. **PROPOSED**
- Time-zone handling for source systems (e.g. UNIS): **OPEN**.
- Identifier type (UUID vs integer): **OPEN**.
- Responses never expose internal identifiers or vendor schemas that the client does not need. **PROPOSED**

## 3. Pagination, filtering, sorting
- Every list endpoint is paginated. There are no unbounded lists. **PROPOSED**
- Envelope: `{ "count": n, "next": url|null, "previous": url|null, "results": [...] }`. **PROPOSED**
- Large append-only data (e.g. punches) uses cursor pagination; small lists use page-number pagination. **PROPOSED**
- Default and maximum page sizes: **OPEN**.
- Filters and sort fields come from a per-endpoint allow-list; unknown parameters are rejected or ignored consistently (the plan states which). **PROPOSED**

## 4. Errors
One error envelope, produced by a single DRF exception handler. **PROPOSED** (RFC 9457 problem+json vs a custom envelope: **OPEN**; the fields below apply either way.)

```json
{
  "type": "validation_error",
  "title": "Invalid request",
  "status": 400,
  "code": "invalid",
  "detail": "One or more fields are invalid.",
  "errors": [{ "field": "name", "code": "required", "message": "This field is required." }],
  "request_id": "..."
}
```

| Status | Meaning |
|---|---|
| 400 | Validation failure |
| 401 | Not authenticated |
| 403 | Authenticated but not permitted |
| 404 | Not found (also used where revealing existence would leak data) |
| 409 | Conflict with current state |
| 429 | Rate limited (rate limiting itself is **DEFERRED**) |
| 5xx | Generic message only |

- Errors never contain stack traces, SQL, secrets or internal paths. **CONFIRMED (P5)**
- Every response carries a `request_id` for correlation. **PROPOSED**

## 5. Validation
- The server is authoritative. Serializers validate input shape and field rules; the service layer enforces business invariants. **PROPOSED**
- Frontend validation is a user-experience aid only and is never trusted. **PROPOSED**
- Field-level errors use the `errors[]` format above. **PROPOSED**

## 6. Authentication and authorisation boundaries
- Constitution P5 applies in full: server-side authorisation and least privilege, no access from client input or token claims alone, no tokens in browser storage, no public diagnostic endpoints in production. It is not restated here.
- Deny by default: the DRF default permission is "authenticated"; each endpoint declares its permission explicitly, and public endpoints are an explicit, justified exception. **PROPOSED**
- Object-level checks are performed in the backend. **PROPOSED**
- Identity provider, session vs token mechanism, roles and permissions model: **OPEN** (needs its own spec).
- Auditable security events, audit retention, access-revocation targets: **OPEN (P5)**.

## 7. Contract
- Each feature's `plan.md` §4 holds its API contract, one block per endpoint (template in `sdd-templates/plan-template.md`). **PROPOSED**
- Generated OpenAPI and TypeScript types would need new dependencies (e.g. drf-spectacular, openapi-typescript): **OPEN**, requires owner approval (P7).

## 8. Cross-cutting items not yet decided
Idempotency keys, CORS/CSRF settings, rate limiting, caching, background jobs, real-time (SSE/WebSocket): **OPEN / DEFERRED**. A feature that needs one must raise it as an OPEN question in its spec.
