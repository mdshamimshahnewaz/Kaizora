# Timely V4 — Feature Prompt

> **How to use:** copy everything below the line into the chat, fill in the five fields, and send. Nothing else needs repeating: the rules are in `AGENTS.md` (loaded automatically) and `docs/sdd-workflow.md`. To move between stages, use the phrases in `sdd-templates/stage-prompts.md`.

---

# Timely V4 — Feature SDD Request

## Feature Input
* Feature name: [FEATURE_NAME]
* Objective: [WHAT IT SHOULD ACHIEVE]
* Scope: [IN SCOPE]
* Out of scope: [OUT OF SCOPE]
* Special requirements: [OPTIONAL]

## Instructions
Follow `AGENTS.md`, `docs/constitution.md`, `docs/sdd-workflow.md` and the project documentation under `docs/`. Inspect the existing codebase (read-only) before proposing anything.

Start with the **specification only**:
1. Draft the spec in the conversation using the structure of `sdd-templates/spec-template.md`: user stories, functional and non-functional requirements, security considerations, dependencies, edge cases and testable acceptance criteria.
2. Propose the next feature folder name (`specs/NNN-slug/`) for me to confirm.
3. List every unresolved decision as OPEN with options and a recommendation. Do not guess.
4. Do not create or modify any file, plan, task or code. Stop and wait for my approval.

Use the feature input above as the only feature-specific scope. Do not assume that features mentioned elsewhere are included.
