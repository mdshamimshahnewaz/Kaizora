# Feature index

Updated: 2026-10-18. Read [workflow](../sdd-workflow.md),
[guide](../sdd-guide.md) and [templates](../../sdd-templates/README.md).
Stages and owner acceptance are separate. Legacy entries preserve recorded evidence;
no retrospective approval or fresh test run is implied.

| ID | Feature / documents | State and evidence | Owner closure |
| --- | --- | --- | --- |
| 0001 | [Development foundation](0001-foundation/spec.md) | Implemented; [recorded verification](0001-foundation/verification.md), with limits; original connection screen later superseded by 0002 | Not recorded here |
| Legacy UI | [UI foundations](../../frontend/docs/ui-foundation-spec.md) | Implemented; spec and [design-system record](../../frontend/docs/design-system.md) retained at original paths | Not recorded here |
| 0002 | [Session login, shell and logout](0002-session-shell/spec.md) | Implemented; [recorded verification](0002-session-shell/verification.md), including follow-ups and browser limitations | Not recorded here |
| 0003 | [Organizations & Membership](0003-organizations-membership/spec.md) | Implemented with live 0004 policy and member-management UI; [verification](0003-organizations-membership/verification.md) | Spec and implementation authorised; owner closure pending |
| 0004 | [Roles & Permissions](0004-roles-permissions/spec.md) | Implemented catalog, roles, assignments and 0003 integration; [verification](0004-roles-permissions/verification.md) | Full scope and implementation approved; owner closure pending |
| 0005 | [Account & Preferences](0005-account-preferences/spec.md) | Implemented in App UI and Django Admin; [delivery evidence](0005-0008-delivery.md) | Implementation authorized; UI/UX acceptance pending |
| 0006 | [Clients & Contacts](0006-clients-contacts/spec.md) | Implemented in App UI and Django Admin; [delivery evidence](0005-0008-delivery.md) | Implementation authorized; UI/UX acceptance pending |
| 0007 | [People & Teams](0007-people-teams/spec.md) | Implemented in App UI and Django Admin; [delivery evidence](0005-0008-delivery.md) | Implementation authorized; UI/UX acceptance pending |
| 0008 | [Projects Foundation](0008-projects-foundation/spec.md) | Implemented in App UI and Django Admin; [delivery evidence](0005-0008-delivery.md) | Implementation authorized; UI/UX acceptance pending |

Next available number: 0010. The initial planning batch has now been implemented through Projects foundation.
Read [the batch review guide](../reviews/2026-10-18-basic-modules.md) for recommended
original planning context. Use the [full-flow review guide](../foundation-flow-review.md) for current UI/Admin review and the delivery record for current readiness limits.

## Required historical/permission scenarios where applicable
- Removed contributors remain in authorised historical reports.
- Mid-month billability changes affect only their effective period.
- Backdated work uses work-date rules, not today's classification.
- Karim 16 non-billable hours + Rahim 8 billable hours = 24 effort / 8 eligible hours.
- Client attribution does not rewrite the actual worker.
- Issued financial records use traceable adjustments.
- Cross-tenant requests cannot read or mutate another tenant's data.
- Retired custom fields/options preserve historical interpretation and access control.

## Documentation transition
2026-10-18: adopted the fuller Timely-inspired project docs and templates, retaining
Kaizora's `design.md` / `verification.md` and four-digit numbering. Future work follows
the new structure. Existing evidence is not rewritten as if those templates existed
at implementation time. Documentation-only verification is in
[the migration record](../sdd-migration-2026-10-18.md).

## 0009 — Simple resource selection / Project Workforce

[Spec](0009-resource-selection/spec.md) · [Design](0009-resource-selection/design.md) · [Tasks](0009-resource-selection/tasks.md) · [Verification](0009-resource-selection/verification.md). Implementation authorized; owner acceptance pending.
