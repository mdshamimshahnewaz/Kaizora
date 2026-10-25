# Verification — Account & Preferences

Implementation authorized: 2026-10-18, App UI and Django Admin.
Owner UI/UX acceptance: pending. Production readiness is not claimed.
[Batch decisions and integration evidence](../0005-0008-delivery.md) ·
[Full-flow review guide](../../foundation-flow-review.md)

## Executed feature checks

| Coverage | Result | Evidence |
| --- | --- | --- |
| Self-only API / field allow-list | Passed | test_account_api_self_scope_and_csrf; no target user parameter accepted. |
| Atomic update / validation / revision | Passed | test_account_atomic_update_and_stale_guard; invalid timezone rolls back name change. |
| Admin profile / preferences | Passed | test_account_timezone_inheritance_and_admin_revision; actual Admin POSTs, stale UserAdmin form rejection. |
| Timezone / presentation | Passed within foundation | Account fallback test and People link timestamp personal-timezone test; business dates remain date fields. |
| Frontend retry / conflict / shell | Passed | account-page.test.tsx plus app.test.tsx; account-provider integration. |

3 focused PostgreSQL tests; account + app frontend checks passed. Anonymous/CSRF protection is exercised. Browser Profile/Preferences loaded, without submitting changes.

Tests use an isolated PostgreSQL test database and frontend API boundary mocks.
The original draft proposed broader production performance, browser mutation and
retention checks. No production workload benchmark or retention approval has been
performed. Existing-session browser work is form/layout inspection only; automated
API/Admin tests provide mutation evidence. Final integrated check totals are in
the batch delivery record. Review spec/design for the complete acceptance criteria.

## Remaining acceptance

Owner reviews ease of use and complete flow before closing this feature.
D-012 workload targets and D-013 retention remain open. Downstream work/time/billing
snapshots do not exist in this foundation and cannot yet be tested end-to-end.


## User-guide follow-up — 2026-10-18

Owner requested configuration/examples and mandatory guide delivery. The [user guide](../../user-guide/README.md) now covers this feature in `account`. [Guide verification](../../user-guide/verification.md) records content/interaction/build checks and the unverified browser visual pass. This follow-up does not change prior implementation evidence or imply owner acceptance.
