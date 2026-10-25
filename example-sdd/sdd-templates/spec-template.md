# Feature Spec — [FEATURE NAME]

> **Purpose:** WHAT is being built and WHY, with no technical solution. Implementation details (database, framework, class names, endpoint shapes) belong in `plan.md`.
> **Location:** `specs/NNN-slug/spec.md`. **Rules:** `docs/constitution.md`, `docs/architecture.md`.
> Mark every decision CONFIRMED, PROPOSED, OPEN or DEFERRED. Do not invent requirements, permissions or owners.
> Workflow and gates: `docs/sdd-workflow.md`. The spec is first drafted in the conversation; this file is written only after the owner approves it.

## 1. Summary
One paragraph: what is this feature and who is it for?

## 2. User Stories
Format: *As a [role], I want [capability], so that [benefit].* Priority: `P0` (must-have), `P1`, `P2`.

- **US-1 (P0):** As a ___, I want ___, so that ___.
- **US-2 (P1):** As a ___, I want ___, so that ___.

## 3. Acceptance Criteria
Concrete, testable criteria per story (Given/When/Then). Include permission cases (who is allowed, who is refused).

### US-1
- **AC-1.1:** Given ___, when ___, then ___.
- **AC-1.2:** Given a user without permission, when ___, then access is refused.

## 4. Operations Clients Need
The business operations the frontend must be able to perform or read (described in plain language, not as endpoints). How they are served is decided in `plan.md`.

| Operation | Who may perform it | Related AC |
|---|---|---|
| [e.g. List a user's attendance records] | [role/owner — do not invent; mark OPEN if unknown] | AC-1.1 |

## 5. Data and Ownership (business level)
- Data this feature creates, reads or changes, and who owns it: [...]
- Sensitivity (personal data, security-relevant): [...]
- Retention/freshness requirements: [...] (or OPEN)

## 6. External Systems and Dependencies
- External systems involved (ORBIS, UNIS, Entra/Graph, AI) and what is needed from each, in business terms. Write "None" if none. (Access is always through backend adapters; see `plan.md`.)
- Dependencies on other features, modules or decisions: [...]

## 7. Non-Functional Requirements
- Performance: [...]
- Security/permissions: [...]
- Auditability (security-relevant events to record): [...]
- Accessibility/i18n: [...]

## 8. Edge Cases & Error States
Invalid input, empty states, unauthorised access, external system unavailable, concurrent edits, etc.
- [...]

## 9. Out of Scope
- [...]

## 10. Open Questions
Anything ambiguous that needs an owner decision. Every item must be resolved or explicitly DEFERRED by the owner before the plan is approved. Do not guess.
- [...]

## 11. Change Log
Changes after approval require re-approval (see `docs/sdd-workflow.md` §5).

| Date | Change | Reason | Approved by |
|---|---|---|---|
| — | — | — | — |

---
**Status:** Draft / Ready for approval / Approved · **Approved by:** [name] · **Date:** [date] · **Linked constitution:** `docs/constitution.md` (v[...])
