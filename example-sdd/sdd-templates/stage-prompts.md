# Timely V4 — Stage Prompts

> Fixed phrases for moving a feature through the SDD gates, so approvals are never ambiguous. Authority: `docs/sdd-workflow.md` §1 and `docs/decisions.md` D-6.
> Each phrase does only what is listed. After doing it, the agent stops and waits.
> A bare "yes", "ok" or "approved" is not enough when more than one thing is pending: the agent must ask which gate you mean.

| Phrase | Agent does | Agent does not |
|---|---|---|
| `SPEC APPROVED` | Creates `specs/NNN-slug/`, writes `spec.md` exactly as approved with status `Approved` (by owner, date), updates `specs/README.md`. | Start the plan. |
| `START PLAN` | Drafts `plan.md` from the approved spec, marks it `Ready for approval`. | Write tasks or code. |
| `PLAN APPROVED` | Records approval in `plan.md` and `specs/README.md`. | Start the tasks. |
| `START TASKS` | Drafts `tasks.md` from the approved plan, marks it `Ready for approval`. | Write code. |
| `TASKS APPROVED` | Records approval in `tasks.md` and `specs/README.md`. | Implement anything. |
| `IMPLEMENT` | Implements only the approved tasks, runs the relevant tests and checks, writes `validation.md` (planned and executed results separate) as `Ready for approval`. Records "Implementation authorised" in `tasks.md`. | Add work outside the approved tasks, or mark a criterion passed without execution evidence. |
| `VALIDATION APPROVED` | Records approval, closes the feature in `specs/README.md`. | Start another feature. |
| `CHANGES REQUESTED: <details>` | Revises the current document or draft and keeps it unapproved. | Move to the next stage. |
| `RESUME NNN-slug` | Reads `AGENTS.md`, `specs/README.md` and the feature folder, reports the current stage and what is waiting for the owner. | Change any file or start any stage. |

Rules:
- Approval and "start the next stage" may be combined in one message (e.g. `SPEC APPROVED. START PLAN.`).
- `IMPLEMENT` must be its own explicit message and must not be combined with `TASKS APPROVED` (D-6).
- Changes to an approved spec, plan or tasks need `CHANGES REQUESTED` and re-approval before work continues (`docs/sdd-workflow.md` §5).
- Only you decide decisions. Agents never mark anything CONFIRMED or `Approved` on their own initiative.
