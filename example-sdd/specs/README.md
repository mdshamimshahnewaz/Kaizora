# Specs Index

Each feature has its own directory `specs/NNN-slug/` containing `spec.md`, `plan.md`, `tasks.md` and `validation.md`. Numbers are 3-digit and sequential, slugs are kebab-case, and folders are never renamed or reused. Workflow, gates and status vocabulary: `docs/sdd-workflow.md`. Templates: `sdd-templates/`.

This file is an index only. Approver names and dates live in each document's footer, not here.

| # | Feature | Stage | Approved through | Implementation authorised | Validation |
|---|---|---|---|---|---|
| 001 | [UI Foundation](001-ui-foundation/) | Implement & Validate | Tasks (v2 + v3 visual correction) | Yes | **Closed 2026-10-11.** Validation approved by the owner. Manual checks not executed are listed as limitations in validation.md |
| 002 | [Authentication](002-authentication/) | Closed | Spec, Plan, Tasks incl. Amendment A-1 (2026-10-13) | Yes | **Closed 2026-10-13.** Validation approved by the owner. Partial or Not-executed manual checks and the idle-expiry audit gap are listed as limitations in validation.md §6 |

| 003 | [About Page](003-about-page/) | Closed | Spec, Plan, Tasks (2026-10-13) | Yes | **Closed 2026-10-13.** Validation approved by the owner. Partial or Not-executed manual checks are listed as limitations in validation.md §6 |
| 004 | [Attendance Sync](004-attendance-sync/) | Implement & Validate; **A-1, A-2 (setup page) and A-3 (menu order, README) implemented; **A-4 (raw punch menu) implemented, validation approved 2026-10-15**, validation approved 2026-10-15 (with limitations)** | Spec, Plan, Tasks (2026-10-14); Amendment A-1 (spec, plan ?13a, tasks T24?T42) approved 2026-10-15 | Yes (T0?T23 and A-1, 2026-10-14/15) | Not approved yet: T22/T41 Partial. All 3 offices verified on real UNIS (one day); open: browser walkthrough, auto-start sign-in test, mid-run outage, historical backfill (needs approval) |
| 005 | [Employee Sync](005-employee-sync/) | Plan (ready for approval) | Spec + Amendment A-1 (2026-10-15) | No | Not started. Plan §8a lists items P-1 to P-6 (incl. OQ-11 permission names) for the owner's decision |

- **Stage:** Spec · Plan · Tasks · Implement & Validate · Closed.
- **Approved through:** the last stage the owner approved (None / Spec / Plan / Tasks).
- **Implementation authorised:** Yes only after the owner's separate explicit instruction (`docs/decisions.md` D-6).
- **Validation:** Not started · Ready for approval · Approved.
- Link each feature name to its directory when a row is added.

> The early architecture draft is archived at `docs/archive/blueprint.md` and is non-authoritative. See `docs/decisions.md` D-9.
