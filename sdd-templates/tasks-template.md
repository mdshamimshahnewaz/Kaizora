# Tasks — NNNN feature

Status: Draft · Design: `design.md` (in the destination feature folder) · Implementation authority: [actual request]

Use [ ] pending, [x] complete; annotate blocked/in-progress tasks in text.
Each unit must be independently verifiable and mapped to acceptance criteria.

- [ ] T-01 — [Concrete change]
  - Depends on: none / task IDs / decision IDs.
  - Implements: AC-1; design section [name].
  - Files/scope: [bounded area].
  - Done when: [observable check and evidence destination].
- [ ] T-02 — Verify and reconcile contracts/docs.
  - Depends on: T-01.
  - Implements: all applicable ACs.
  - Done when: verification.md records executed results and gaps per AC; generated
    contracts are current; feature index reflects actual state.
- [ ] T-03 — Deliver the end-user guide with the feature.
  - Depends on: T-01.
  - Files/scope: frontend/public/user-guide/index.html and docs/user-guide/README.md.
  - Done when: UI/Admin steps, setup, permissions, examples, expected results, history,
    errors and limitations match implemented behaviour; verification.md links sections
    and checks. Internal-only changes require an explicit no-user-impact rationale.

## Change log
| Date | Task changes | Reason | User direction / approval |
| --- | --- | --- | --- |
