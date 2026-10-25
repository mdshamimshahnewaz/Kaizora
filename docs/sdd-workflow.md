# Kaizora SDD workflow

Adapted from Timely on 2026-10-18. Existing Kaizora paths and evidence are preserved.
Sequence: Constitution → Spec → Design → Tasks → Implement → Verify → Owner review.
Timely's `plan.md` maps to our `design.md`; `validation.md` maps to `verification.md`.
Do not maintain duplicate versions under both names.

## Authorisation and stages
For a staged request, produce only the requested stage and identify unresolved choices.
For an explicit end-to-end implementation request, draft the spec/design/tasks before
code and proceed within that authorisation; do not request the same permission at
every stage. Ask for decisions that materially change scope, security or business
policy. An approval of a document alone is not an instruction to build an unrequested
feature. Files may be saved as drafts for review. Never invent owner approval.

| Stage | Output | Completion evidence |
| --- | --- | --- |
| Specify | spec.md | Users, scope, AC IDs, domain rules and open questions |
| Design | design.md | Ownership, interfaces, API, migration, UI and test mapping |
| Break down | tasks.md | Task IDs, dependencies, AC links, done conditions |
| Implement | Code, meaningful tests and user guide | Authorised tasks completed; scope respected |
| Verify | verification.md | AC-level executed evidence and explicit gaps |
| Review/close | Index and change log | Owner acceptance recorded only when actually given |

## Locations and status
Use `docs/specs/NNNN-slug/` with four-digit sequential IDs, never reused. Existing
0001/0002 keep their names. Templates are in `sdd-templates/`. Update the feature
index at stage transitions. The older UI foundation stays in frontend/docs and is
indexed as legacy evidence; do not invent a retrospective approval or test run.

Document statuses: Draft, Ready for review, Approved (only actual owner approval).
Feature stages: Spec, Design, Tasks, Implementing, Verified, Review pending, Closed.
A verified implementation is not automatically owner-accepted or production-ready.
Decision labels and provenance follow decisions.md.

## Change control
Before changing agreed behaviour, update its acceptance/design and affected task/test
mapping. Record date, reason, authority and affected ACs. Reassess downstream contracts,
migrations and evidence. Seek owner input for a new material choice outside authorised
scope; already-requested revisions need no duplicate permission. Preserve old evidence
with its date; never present a stale run as verification of a new revision.

## Small-change path
A cosmetic or editorial change with no API, permission, financial or historical
behaviour change may use a dated entry in the relevant verification/change record:
request, files, expected result, executed check and limitations. Security, migrations,
historical rules and API changes require the full feature path. Do not disguise a
behaviour change as a cosmetic fix.

## Completion and safety
Every acceptance row is Passed, Failed, Partial or Not executed, with evidence.
Deferred work must identify reason and follow-up; failing required behaviour prevents
a claim of completion unless the owner explicitly accepts a scoped limitation.
Separate production prerequisites from local verification. Never create fake approval
records, copy Timely test results, expose secrets or rewrite historical evidence.
No commit/push/PR or server startup is implied by this documentation workflow.


## Mandatory user-guide delivery (owner instruction, 2026-10-18)

Each user-facing feature is delivered with its guide update, not as a later task.
Update the canonical `frontend/public/user-guide/index.html` and its coverage map
in `docs/user-guide/README.md`. Include entry points, actors/permissions, prerequisite
configuration, field examples, UI and applicable Django Admin steps, expected results,
lifecycle/history effects, conflict/error recovery and current limitations.
Do not include real credentials, private data or claim unimplemented functionality.
Preserve guide anchors when possible. Check links, search, narrow layout and build
packaging when changing the guide UI; verify instructions against current code/UI.
The feature's verification.md must link its guide sections and record actual checks.
Missing guide means user-facing delivery is incomplete. For an internal-only change,
record an explicit no-user-impact justification rather than inventing workflow steps.
