---
title: Complete business features through application UI and Django Admin
date: "2026-10-18"
category: workflow-issues
module: Feature delivery
problem_type: workflow_issue
component: development_workflow
severity: medium
root_cause: missing_workflow_step
resolution_type: workflow_improvement
applies_when:
  - "Designing or implementing user-facing business-management features"
  - "Reviewing SDD completion and handoff claims"
tags: [feature-completeness, django-admin, frontend, sdd, acceptance]
---

# Complete business features through application UI and Django Admin

## Context

Features 0003 and 0004 were initially treated as delivered while organization
creation depended on API/CLI access and relevant Django Admin models were
read-only. The user corrected the delivery expectation: “BHai ami to UI and
admin theke eisob banaite chai” — they need to create and manage these records
through the application and Admin. They then explicitly requested that this
mistake be recorded for future feature work.

The root cause was accepting technical-layer completion without checking the
human workflow. An earlier assistant-authored design restriction had narrowed
the intended product experience. Passing API tests did not close that gap.

## Guidance

Before implementation, map each approved business action to its actor, entry
surface, permission, successful outcome, and acceptance evidence in the SDD.
For this project, default user-facing management features to application UI
and appropriate Django Admin operational workflows. Honor explicit user scope
exceptions; do not silently substitute CLI commands for these workflows or
treat an older design limitation as overriding the user's clarification.

Before reporting a feature complete:

1. Verify that authorized users can discover and finish the approved actions
   from navigation and forms, including required creation and editing flows.
2. Verify UI capability gating and server-side authorization separately. A
   hidden button alone is not access control. Cover denied and cross-tenant
   requests where relevant.
3. Route API and Admin mutations through the module's shared commands so that
   validation, permissions, concurrency checks and history remain consistent.
   Do not use unrestricted model saves to make Admin appear functional.
4. Cover loading, empty, validation-error, disabled/pending and stale-data
   behavior where applicable. Check history preservation for changes affecting
   membership, assignment, billing or other historical records.
5. Run relevant tests, type/lint/build checks and inspect affected browser
   flows. Record exactly which mutations were exercised and in which test
   environment; inspecting a form is not proof of a successful live mutation.
6. Reconcile the SDD tasks and verification evidence with the actual delivery.
   State any unimplemented workflow, unverified behavior or pending user
   acceptance explicitly. Do not equate local verification with production
   readiness, user acceptance or a guarantee of zero defects.

This is not a blanket requirement to expose every database table as editable
CRUD. Audit events and raw policy records may deliberately remain read-only.
Describe those decisions, and provide safe business commands for the actions
the user actually needs. Do not expand into unapproved future modules.

## Why This Matters

The user's unit of value is an action they can complete, such as creating an
organization and assigning its owner. API availability alone leaves that work
unfinished. Command-backed Admin forms avoid the false choice between a safe
but unusable read-only interface and unsafe direct model edits.

## When to Apply

- During feature design and task decomposition, before surface gaps are built in.
- During implementation and final review of business-management workflows.
- When user feedback contradicts an earlier SDD scope assumption.

## Examples

| Action | Expected delivery | Evidence to collect |
| --- | --- | --- |
| Create organization | Application form and authorized Admin form using the shared creation command | Success, invalid owner, unauthorized caller, and owner/history outcome |
| Change membership access | Authorized application and Admin workflows | Status transition, stale-version rejection, preserved identity/history |
| Inspect audit history | Authorized read-only access as specified | Visibility and protection from mutation; no generic edit form required |

The corrected organization UI reads the provisioning capability before showing
its creation action and submits through the API in
`frontend/src/features/organizations/create-organization.tsx`.
`backend/common/admin.py` supplies command-backed add/change forms: it checks
Admin permissions, invokes the command adapter, and presents API errors as form
errors. The organization commands in
`backend/modules/organizations/interfaces.py` enforce provisioning authority,
validate the owner, record creation history, and reject stale membership changes.

The session's follow-up verification records 37 backend and 22 frontend tests
passing, plus typecheck, lint, production build, Django and boundary checks.
Browser inspection covered both creation forms without submitting live data;
automated tests supplied mutation evidence. These are recorded local results,
not a claim that all future features or production scenarios are verified.
See the [verification follow-up](../../specs/0004-roles-permissions/verification.md).

## Related

- [SDD workflow and completion stages](../../sdd-workflow.md)
- [SDD acceptance and evidence guidance](../../sdd-guide.md)
- [Organization design and UI/Admin correction](../../specs/0003-organizations-membership/design.md)
- [Permissions design and UI/Admin correction](../../specs/0004-roles-permissions/design.md)
- [Current UI/Admin usage instructions](../../roles-membership-usage.md)
- [Shared domain vocabulary](../../../CONCEPTS.md)
