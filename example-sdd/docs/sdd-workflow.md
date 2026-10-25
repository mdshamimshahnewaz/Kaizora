# Timely V4 — SDD Workflow

> **Authority:** Subordinate to `docs/constitution.md` (P1, P2, P6). Decisions behind this document: `docs/decisions.md` D-2, D-6, D-7, D-16, D-17, D-19.
> **Legacy:** the files in `docs/archive/` are non-authoritative. Do not follow them.

## 1. Stages and approval gates
```
Constitution → Spec → Plan → Tasks → Implement & Validate
```

| Stage | Output | Starts only when the owner… | Ends when the owner… |
|---|---|---|---|
| Constitution | `docs/constitution.md` (amendments only) | explicitly asks for an amendment | approves it; the amendment log is updated |
| Spec | `specs/NNN-slug/spec.md` | asks to start the spec | approves the spec |
| Plan | `plan.md` | asks to start the plan | approves the plan |
| Tasks | `tasks.md` | asks to start the tasks | approves the task list |
| Implement & Validate | code, tests, `validation.md` | **separately and explicitly instructs implementation to begin** | approves `validation.md` (feature closed) |

Gate rules:
1. Approving a document does not authorise the next stage. The owner must also ask to proceed (P1).
2. Approving `tasks.md` does **not** authorise implementation. The owner gives one explicit implementation instruction per feature (D-6).
3. Agents never mark a document `Approved` or a decision CONFIRMED on their own initiative. The spec is drafted in the conversation and no file is written until the owner approves it. Plan, tasks and validation are written as files marked `Ready for approval`, and the agent then stops and waits. After the owner's explicit approval phrase (`sdd-templates/stage-prompts.md`), the agent records "Approved by owner, date".
4. No stage may be skipped, merged or started early. Existing foundation code that predates the Constitution is exempt only until a feature changes it (P1).
5. Every change traces to an approved task, and every task to an approved spec item.

## 2. Where things live
| Location | Contents |
|---|---|
| `docs/` | Shared rules: Constitution, architecture, API conventions, frontend API client rules, decision log, this workflow. |
| `specs/NNN-slug/` | One directory per feature: `spec.md`, `plan.md`, `tasks.md`, `validation.md`. |
| `specs/README.md` | Index of features and their stage. |
| `sdd-templates/` | Reusable templates, the feature prompt (`feature-prompt.md`) and the stage phrases (`stage-prompts.md`). Copy a template into the feature directory and fill it in. |

Feature folders use a 3-digit sequential number and a kebab-case slug (e.g. `specs/001-attendance-list/`). Numbers are never reused and folders are never renamed (D-16).

## 3. Creating a feature
1. On the owner's feature input (`sdd-templates/feature-prompt.md`), propose the next `NNN-slug` for the owner to confirm. Create no files yet.
2. Spec: draft it in the conversation using the structure of `spec-template.md` (WHAT and WHY only). List every OPEN question; each must be resolved or explicitly DEFERRED by the owner before the plan is approved. Stop. Only after the owner approves, create `specs/NNN-slug/` and write `spec.md`.
3. Plan: copy `plan-template.md`. It covers API contracts, data ownership, security, external systems, BFF justification and testing. Stop and ask for approval.
4. Tasks: copy `tasks-template.md`. Stop and ask for approval.
5. Wait for the owner's explicit instruction to implement.
6. Implement task by task, with tests. Do not add work outside the approved tasks.
7. Validate: copy `validation-checklist-template.md`. Report planned and executed validation separately, with recorded results (P6). Stop and ask for approval.
8. Update `specs/README.md` at the end of every stage.

## 4. Status vocabulary and approval record
- Document status: `Draft → Ready for approval → Approved` (D-7). There is no "Reviewed" status.
- Each document footer records `Status`, `Approved by` and `Date`. Only the owner sets `Approved`.
- Decision labels: CONFIRMED, PROPOSED, OPEN, DEFERRED. Only the owner promotes a decision to CONFIRMED (P2). Agents flag contradictions instead of choosing a side.

## 5. Change control (D-19)
- Any change to an approved spec, plan or tasks document needs the owner's approval before the change is made, and the document returns to `Ready for approval`.
- Record each change in the document's Change Log (date, what, why, approver).
- Documents downstream of the changed one are re-checked and re-approved if affected. Implementation pauses until re-approval.
- Constitution amendments follow its §6 and its amendment log.

## 6. Git policy (D-17)
- A root `.gitignore` must exist before anything is staged.
- The owner directs when to commit. Agents never commit, push or open pull requests unless asked.
- Never stage `.env` files or other secrets.

## 7. Rules
- Specs do not invent requirements, permissions, tenant details or owners (P2).
- Do not add dependencies or infrastructure without approval (P7).
- A feature that conflicts with the Constitution or `docs/` rules is stopped and raised, not worked around.
- A requirement is "Passed" only when its test or validation was actually run and the result recorded (P6).
- Before writing frontend code, read the Next.js documentation in `frontend/node_modules/next/dist/docs/` (see `frontend/AGENTS.md`).
