# Technical Plan — [FEATURE NAME]

> **Purpose:** HOW the approved `spec.md` will be implemented. Every decision traces to a spec item.
> **Location:** `specs/NNN-slug/plan.md`. **Rules:** `docs/constitution.md`, `docs/architecture.md`, `docs/api-conventions.md`, `docs/frontend-api-client.md`.
> Mark every decision CONFIRMED, PROPOSED, OPEN or DEFERRED. Do not depend on an OPEN decision without flagging it.
> Workflow and gates: `docs/sdd-workflow.md`. Start only when the owner asks for the plan. Stop after writing it and wait for approval.

## 1. Linked Spec
Source: `specs/NNN-slug/spec.md` · Covers: [US-1, US-2, ...]

## 2. Architecture Overview
How the feature fits the system: backend module(s), service layer, frontend pages/components, adapters. Keep within API-first (P8): Next.js presents, Django holds logic and data access.

## 3. Data Model and Ownership
```
Entity: [Name]            Owner module: [module]
  field: type — constraints — purpose
Relationships: [...]
```
- Owning module for each entity/table: [...]
- Other modules that need this data, and the internal interface they use: [...]
- How this feature references another module's data (no importing its models or tables): [...]
- Migrations: [...]

## 4. API Contract
One block per endpoint. Follow `docs/api-conventions.md`.

```
[METHOD] /api/v1/<module>/<resource>/
  Purpose:        [...] (spec: US-x / AC-x.x)
  Auth:           [authenticated / public + justification]
  Permission:     [exact rule, incl. object-level checks]
  Request:        [fields, types, validation rules]
  Response 2xx:   [fields]
  Pagination/filter/sort: [...]
  Errors:         [400 / 401 / 403 / 404 / 409 — when each occurs]
```
Internal module interfaces (not HTTP): [functions/classes, inputs, outputs].

## 5. Security
- Authentication and authorisation per endpoint (server-side, deny by default): [...]
- Input validation and where invariants are enforced: [...]
- Sensitive data handling; nothing secret in logs, responses or docs: [...]
- Audit events recorded: [...]

## 6. External Systems and Adapters
Adapter(s) used, port/interface, read/write direction (UNIS is read-only), failure behaviour, secrets/config via environment. Write "None" if none.

## 7. Frontend
- Pages/components and which shared-client functions they call (`frontend/lib/api/`): [...]
- Error and empty-state handling: [...]
- **BFF / Route Handlers:** None — or justification per handler (why Django alone is not enough, what it does, what it must not do) and its entry in the register in `docs/architecture.md` §3.

## 8. Tech Choices & Trade-offs
| Decision | Options considered | Chosen | Status | Why |
|---|---|---|---|---|
| [...] | [...] | [...] | PROPOSED | [...] |

New dependencies or infrastructure require owner approval (P7); list them here or write "None".

## 9. Traceability Matrix
| Spec item | Plan section | Notes |
|---|---|---|
| US-1 / AC-1.1 | §3, §4 | [...] |

## 10. Testing Strategy
- Backend service/unit tests: [...]
- API tests (contract, permissions, validation, error shapes, pagination): [...]
- Frontend client/component tests: [...]
- Adapter tests (mocked external systems): [...]
- Manual verification: [...]
Each acceptance criterion has an automated test where feasible (P6).

## 11. Risks & Mitigations
- [Risk] → [Mitigation]

## 12. Constitution Check
List every principle currently in `docs/constitution.md` (do not rely on a fixed list) and state compliance.

| Principle | Compliant? | Notes |
|---|---|---|
| [P1] | | |
| [P2] | | |
| [...] | | |

## 13. Change Log
Changes after approval require re-approval (see `docs/sdd-workflow.md` §5).

| Date | Change | Reason | Approved by |
|---|---|---|---|
| — | — | — | — |

---
**Status:** Draft / Ready for approval / Approved · **Approved by:** [name] · **Date:** [date]
