# Task Breakdown — [FEATURE NAME]

> **Purpose:** Break the approved `plan.md` into small, ordered, independently verifiable tasks (ideally under one day each), each with a pass/fail condition.
> **Location:** `specs/NNN-slug/tasks.md`. Start only when the owner asks for the tasks, and stop after writing them.
> **Approval does not authorise implementation.** Implementation starts only after the owner approves this list **and** gives a separate explicit instruction to implement (`docs/decisions.md` D-6).

## Conventions
- `[ ]` pending, `[x]` done, `[~]` in progress, `[!]` blocked (explain why).
- Each task references the plan section and spec item it implements.
- Group tasks by area. The list order is the execution order.

## Backend
- [ ] **T1 — [Title]** _(depends on: none)_
  - Implements: Plan §[...], Spec [US-x / AC-x.x]
  - Done when: [concrete, checkable condition]

## API contract
- [ ] **T2 — [Title]** _(depends on: T1)_
  - Implements: Plan §4
  - Done when: [endpoint behaves per contract, including permissions and errors]

## External adapters (if any)
- [ ] **T3 — [Title]** _(depends on: ...)_
  - Implements: Plan §6
  - Done when: [...]

## Frontend
- [ ] **T4 — [Title]** _(depends on: T2)_
  - Implements: Plan §7
  - Done when: [uses the shared API client only; no direct Django `fetch`, no DB access]

## Tests and validation
- [ ] **T_n — Write and run tests for all acceptance criteria** _(depends on: implementation tasks)_
  - Implements: Plan §10
  - Done when: every AC has a passing automated test where feasible, and results are recorded.

- [ ] **T_final — Validation pass** _(depends on: T_n)_
  - Produces: `validation.md`
  - Done when: every AC is Passed (with executed evidence) or explicitly Deferred with a reason.

## Notes
- Split any task that grows too large.
- Do not add tasks outside the approved plan; raise them for approval.

## Change Log
Changes after approval require re-approval and pause implementation (see `docs/sdd-workflow.md` §5).

| Date | Change | Reason | Approved by |
|---|---|---|---|
| — | — | — | — |

---
**Status:** Draft / Ready for approval / Approved · **Approved by:** [name] · **Date:** [date] · **Implementation authorised by owner:** No / Yes ([date])
