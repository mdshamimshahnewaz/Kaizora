# Timely V4 — SDD User Guide

> **Audience:** the project owner. **Purpose:** a complete, step-by-step guide to running a feature through the SDD workflow, and to reusing the setup in another project.
> **Status:** PROPOSED (a how-to; the rules themselves are in `docs/constitution.md` and `docs/sdd-workflow.md`, which win if they ever disagree with this guide).

## 1. The idea in one minute
Every feature moves through fixed stages. The AI agent does the work of one stage, then **stops**. Nothing moves forward until you say so, in a fixed phrase.

```
Constitution → Spec → Plan → Tasks → Implement & Validate
   (once)      you approve each stage; you also say "go" for the next one
```

Three things you control:
1. **Approval** of each document (`SPEC APPROVED`, `PLAN APPROVED`, `TASKS APPROVED`, `VALIDATION APPROVED`).
2. **Starting** the next stage (`START PLAN`, `START TASKS`).
3. **Implementation** (`IMPLEMENT`), always its own message, never combined with `TASKS APPROVED`.

The agent never approves anything itself and never confirms a decision. The rules for agents are in `AGENTS.md`, which Copilot CLI loads automatically from the repository root.

## 2. Where everything is
| File / folder | What it is | You use it to |
|---|---|---|
| `docs/constitution.md` | Non-negotiable principles | Change only by explicit amendment |
| `docs/sdd-workflow.md` | Stages, gates, status vocabulary, change control, Git policy | Look up a rule |
| `docs/architecture.md`, `api-conventions.md`, `frontend-api-client.md` | Timely V4 technical rules (PROPOSED) | Check plans against them |
| `docs/tech-stack.md` | Installed stack, commands | Check versions and commands |
| `docs/decisions.md` | All decisions and their status; the register of OPEN items | Answer OPEN questions |
| `AGENTS.md` | Rules the agent follows | Rarely edit |
| `sdd-templates/feature-prompt.md` | The prompt you paste to start a feature | Start a feature |
| `sdd-templates/stage-prompts.md` | The phrases that move a feature between stages | Move between stages |
| `sdd-templates/*-template.md` | Templates for spec, plan, tasks, validation, constitution | Agents copy them |
| `specs/README.md` | Index: every feature, its stage and approvals | See where each feature is |
| `specs/NNN-slug/` | One folder per feature: `spec.md`, `plan.md`, `tasks.md`, `validation.md` | Review documents |

## 3. Running one feature, step by step

### Step 0 — Before you start
- Start a **new chat session** for the feature, from the repository root, so `AGENTS.md` is loaded.
- Know your five inputs: name, objective, scope, out of scope, special requirements.

### Step 1 — Ask for the spec
1. Open `sdd-templates/feature-prompt.md`.
2. Copy everything below the line, fill in the five fields, and send.
3. The agent inspects the code (read-only) and replies **in the conversation** with a draft spec, a proposed folder name (`specs/NNN-slug/`) and a list of OPEN decisions. It writes **no files**.

**Review the spec** (checklist):
- Each user story has a priority (P0/P1/P2) and testable Given/When/Then criteria.
- There is at least one permission or refusal case per protected operation.
- Roles, permissions, data sources and integrations are ones **you** named, not invented.
- Out of scope is explicit. No technology choices appear (that is the plan's job).
- Data ownership and sensitivity are stated. External systems are listed.
- Every OPEN item has options and a recommendation.
- The proposed folder name is acceptable.

Answer the OPEN items. If something is wrong, send `CHANGES REQUESTED: <what to change>`. The agent revises and stops again.

### Step 2 — Approve the spec
Send: `SPEC APPROVED. START PLAN.` (or only `SPEC APPROVED` to pause).
The agent creates `specs/NNN-slug/`, writes `spec.md` exactly as approved (status Approved, by you, with the date), updates `specs/README.md`, and stops (or, if you added `START PLAN`, drafts the plan).

### Step 3 — Review the plan
The agent writes `plan.md` as a file marked **Ready for approval**.

**Review the plan** (checklist):
- Every acceptance criterion appears in the traceability matrix.
- Each endpoint has: method, path, who may call it, exact permission, request and response, validation, pagination, errors.
- One module owns each piece of data; other modules use its internal interface, never its tables.
- External systems are accessed only through backend adapters; the frontend never touches the database or external systems.
- Route Handlers/BFF: "None" or each one justified.
- New dependencies or infrastructure are listed (and need your approval) or "None".
- The testing strategy covers every criterion, by layer.
- The constitution check lists every principle, and any OPEN decision it depends on is flagged.

Send `CHANGES REQUESTED: …` until you are satisfied, then `PLAN APPROVED. START TASKS.`

### Step 4 — Review the tasks
The agent writes `tasks.md` as a file marked **Ready for approval**.

**Review the tasks** (checklist):
- Tasks are small (about a day or less), in dependency order, and each has a concrete "Done when".
- Each traces to a plan section and a spec item.
- There is a test task covering every criterion and a final validation task.
- Nothing is outside the approved plan.

Send `TASKS APPROVED`. **The agent still does not implement anything.**

### Step 5 — Authorise implementation
Send, as a separate message: `IMPLEMENT`.
The agent implements only the approved tasks, runs the tests and checks, and writes `validation.md` (planned and executed results separately) marked Ready for approval. It records "Implementation authorised" in `tasks.md`.

While it works, you can check: `git diff` shows only expected files; no unrelated changes; no secrets; no unapproved dependencies.

### Step 6 — Review the validation
**Review `validation.md`** (checklist):
- Every acceptance criterion shows executed evidence (command, date, result), or is explicitly Deferred with a reason.
- Planned and executed validation are separate. Nothing is "Passed" without a recorded run.
- Failures are explained, not hidden.
- The API-first compliance table and constitution table are filled in with evidence.

Then send `VALIDATION APPROVED`. The feature is closed in `specs/README.md`. If something is wrong, send `CHANGES REQUESTED: …`.

### Step 7 — Commit (your decision)
Agents never commit unless you ask. A suggested rhythm (PROPOSED): one commit per approved stage, for example "docs: approve spec 001-slug", and one or more commits for the implementation. Stage only the paths you intend; never `git add .` while secrets or unfixed files are in the tree.

## 4. Changing something after approval
- Send `CHANGES REQUESTED: …` naming the document. The agent drafts the change, the document goes back to Ready for approval, and **implementation pauses** (`docs/sdd-workflow.md` §5).
- Re-approve the changed document and any documents after it that are affected.
- The change is recorded in that document's change log.

## 5. Picking work back up in a new session
Start a new chat from the repository root and send:

`RESUME NNN-slug` — the agent reads `AGENTS.md`, `specs/README.md` and the feature folder, reports the current stage and what is waiting for you, and stops.

## 6. Quick reference
| Situation | You send |
|---|---|
| Start a feature | the filled `feature-prompt.md` |
| Approve spec and continue | `SPEC APPROVED. START PLAN.` |
| Approve plan and continue | `PLAN APPROVED. START TASKS.` |
| Approve tasks (no coding yet) | `TASKS APPROVED` |
| Allow coding | `IMPLEMENT` |
| Close feature | `VALIDATION APPROVED` |
| Fix something | `CHANGES REQUESTED: <details>` |
| New session | `RESUME NNN-slug` |

**Status words:** documents are `Draft → Ready for approval → Approved`. Decisions are CONFIRMED (you approved), PROPOSED (suggested), OPEN (undecided), DEFERRED (postponed). Only you promote a decision to CONFIRMED.

## 7. If the agent misbehaves
| Problem | What to do |
|---|---|
| It wrote files before the spec was approved | Say `CHANGES REQUESTED: delete what you created before approval and redo as a conversation draft`. Check `git status`. |
| It started the next stage on its own | Tell it to stop. State which gate is current. Agent rules forbid this (`AGENTS.md`). |
| It asks which gate you mean | A bare "yes" or "approved" is ambiguous when several gates are pending. Use the exact phrase. |
| It invented a role, rule or integration | `CHANGES REQUESTED: remove it and list it as an OPEN question`. |
| It wants a new dependency | It must be listed in the plan and approved by you first. |
| It says a criterion passed with no test run | Reject the validation record. |

## 8. Using this setup in another project
**Copy as is (reusable):**
- `sdd-templates/` (all templates, `feature-prompt.md`, `stage-prompts.md`).
- `docs/sdd-workflow.md`.
- This guide.

**Copy, then adapt (project-specific):**
- `AGENTS.md` — keep the gate rules; change the project name, the read order, the stack rules (e.g. "No Docker or WSL", "API-first (P8)", the Next.js note).
- `docs/sdd-workflow.md` — remove the Timely decision-ID references (`D-2`, `D-6`, ...) if the new project has no `decisions.md` yet, and the Next.js docs sentence in §7 if it does not apply.
- `docs/decisions.md` — start empty with the four status headings.
- `specs/README.md` — start with an empty table.

**Do not copy (Timely-specific):** `docs/constitution.md`, `architecture.md`, `api-conventions.md`, `frontend-api-client.md`, `tech-stack.md`, everything under `specs/NNN-slug/`.

**Bootstrap checklist for a new project:**
1. Create the repository. Create a root `.gitignore` **before** staging anything (env files, virtualenvs, caches, local databases).
2. Copy the reusable files above. Create `docs/` and `specs/` folders.
3. Write the constitution. Send: *"Draft `docs/constitution.md` for [project] using `sdd-templates/constitution-template.md`. Mark every principle PROPOSED. Present it in the conversation only and stop."* Edit it with the agent, then approve it. Only then write the file, with status and version.
4. Create `docs/tech-stack.md` (installed versions and commands) and the architecture rules that fit the project. Mark them PROPOSED until you approve them.
5. Adapt `AGENTS.md` (read order, hard rules, environment).
6. Create an empty `docs/decisions.md` and `specs/README.md`.
7. Review everything once, then commit. Start the first feature with `feature-prompt.md`.

## 9. Open points (not decided yet)
- A lighter path for trivial changes (typos, one-line bug fixes). Constitution P1 currently applies to all new work. If you want a lightweight path, decide and record it in `docs/decisions.md`; until then use the full workflow.
- Branch and pull-request policy (the Git policy only covers commits and staging).
