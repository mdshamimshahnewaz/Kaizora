# Verification — 0008 Projects Foundation

Date: 2026-10-18. Implementation authorized and delivered in App UI and Django Admin.
Owner UI/UX acceptance: pending. Production readiness is not claimed.

| Area | Executed evidence |
| --- | --- |
| Creation and client binding | PostgreSQL tests cover delivery/operations, explicit initial manager, wrong/archived clients, duplicate code and atomic rollback. Internal projects are represented by no client, not a third type. |
| Private access | List/detail visibility, forged scope, live role archival, membership suspension, access ending and read_all without management are tested. |
| Lifecycle and revisions | Allowed transitions, archived write protection, stale edits and independent concurrent writer rejection are tested. |
| Admin | Actual create/change/access POSTs exercise shared commands and read-only history. |
| Query growth | Project list, access-history batch hydration and Admin grant list are checked; Admin capability batch matches current private access. |
| Frontend | Project interaction tests cover create, lifecycle/access behavior, conflicts and scoped responses; included in the 46-test integrated suite. |
| Browser | Existing session list/create dialog/role picker inspected; 390px Projects layout has no horizontal overflow. No live mutation submitted. |

Commands, integrated results and review limitations are in the [delivery record](../0005-0008-delivery.md). The backend suite passed 58 tests, frontend 46; typecheck/lint/build, schema validation, migrations and boundaries passed.

The live organization had no eligible initial-manager role. The selector correctly links to Settings & access; create the project-scoped Project manager preset there before creating a project. No automatic grants or seeded roles were added.

Remaining limits: owner acceptance, full browser mutation journey, representative production workload/retention policies and large Admin selector scaling. CE diff review was unavailable because the workspace lacks a committed Git baseline; manual checks and automated tests are recorded separately.


## User-guide follow-up — 2026-10-18

Owner requested configuration/examples and mandatory guide delivery. The [user guide](../../user-guide/README.md) now covers this feature in `projects এবং project-access`. [Guide verification](../../user-guide/verification.md) records content/interaction/build checks and the unverified browser visual pass. This follow-up does not change prior implementation evidence or imply owner acceptance.
