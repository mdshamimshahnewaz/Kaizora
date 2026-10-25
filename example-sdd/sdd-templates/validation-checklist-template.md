# Validation Record — [FEATURE NAME]

> **Purpose:** Prove that each acceptance criterion in `spec.md` is met. A requirement is **Passed** only when its test or validation was actually executed and the result recorded (Constitution P6). Planned and executed validation are reported separately.
> **Location:** `specs/NNN-slug/validation.md`.

## 1. Planned Validation
| Spec ID | Description | Planned test / check |
|---|---|---|
| AC-1.1 | [...] | `path/to/test::name` |

## 2. Executed Validation
Command(s) run, date, and environment: [...]

| Spec ID | Test (file/name) | Result | Evidence / notes |
|---|---|---|---|
| AC-1.1 | `path/to/test::name` | Passed / Failed / Not run / Deferred | [output summary, reason if deferred] |

## 3. API-First Compliance
| Check | Result | Evidence |
|---|---|---|
| Every endpoint matches the plan's API contract (methods, fields, errors, pagination) | | |
| Authentication and permission cases tested, including refusal cases | | |
| Server-side validation and error envelope verified | | |
| Frontend uses only the shared API client; no direct Django `fetch` outside `lib/api/` | | |
| No frontend code accesses PostgreSQL or an external system | | |
| Route Handlers/BFF: none, or each is justified and in the register | | |
| External systems accessed only through backend adapters | | |
| No module accesses another module's models or tables | | |

## 4. Constitution Compliance
List every principle currently in `docs/constitution.md` (do not rely on a fixed list).

| Principle | Result | Evidence |
|---|---|---|
| [P1] | | |
| [P2] | | |
| [...] | | |

## 5. Non-Functional Requirements
- Performance: [...]
- Security: [...]
- Auditability: [...]

## 6. Outcome
Overall status: **Ready for owner sign-off / Needs rework**. Only the owner closes the feature. Gaps, deferred items and follow-up specs: [...]

## 7. Change Log
| Date | Change | Reason | Approved by |
|---|---|---|---|
| — | — | — | — |

---
**Status:** Draft / Ready for approval / Approved · **Approved by:** [name] · **Date:** [date]
