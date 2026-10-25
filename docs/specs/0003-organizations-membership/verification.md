# Verification — 0003 Organizations & Membership

Date: 2026-10-18 (Asia/Dhaka). Implemented and locally verified within 0003 scope.
Owner implementation authority: “Please implement”. Owner closure: not yet recorded.

## Executed automated evidence
- E1: New bootstrap API test failed with 404 before endpoint implementation.
- E2: Full PostgreSQL backend suite: **27 passed**. Uses repository development PostgreSQL
  at port 55432 and its isolated test database, not live user records. Sandbox network
  restriction required execution permission; no PostgreSQL service was started.
- E3: Frontend Vitest suite: **14 passed** (7 existing auth, 7 organization tests).
  These tests mock the API boundary and exercise real components/routes.
- E4: Ruff lint/format, Django system check, static module boundaries and 3 checker tests
  passed. Migration dry-run reports no changes; initial sandbox migration-history probe
  was unavailable. Later configured-DB migration plan/application succeeded.
- E5: OpenAPI generation/validation with fail-on-warn and TypeScript generation passed.
  TypeScript, ESLint and production build passed; no dependency changes.
- E6: Upgrade test migrates organization tables down/up on isolated PostgreSQL, retains
  an existing user and verifies no memberships/organizations are silently created.
- E7: Two independent PostgreSQL connections race owner transfers and last-owner exits;
  one succeeds, the other is denied/conflicts, retaining one active owner.

## Acceptance mapping
| AC | Result | Evidence and scope |
| --- | --- | --- |
| AC-01 | Passed (automated) | E1/E2: provisioning permission, unauthorized denial, rollback when event creation fails; no operator read bypass |
| AC-02 | Passed (automated) | E2: A/B/C visibility, paginated results, inaccessible IDs, forged public scope |
| AC-03 | Passed (automated) | E2: ending membership revokes scope without deleting membership/events; stable identity after reactivation |
| AC-04 | Passed (automated) | E2/E7: atomic transfer, last-owner rejection, simultaneous transfer/removal protection |
| AC-05 | Passed (automated) | E2: duplicate conflict and reactivation of same ID with preserved transition history |
| AC-06 | Passed (component tests) | E3: delayed Alpha response cannot replace Beta; old content cleared immediately on switch |
| AC-07 | Passed (automated) | E2/E3: policy denial, stale version conflict, atomic audit records, malformed/unknown input, CSRF, error/retry states |
| AC-08 | Passed (PostgreSQL) | E2/E6: fresh test schema and upgrade rehearsal; no tenant backfill |

## Configured database and browser
Inspected the configured database migration plan: only organizations.0001_initial was
pending. Applied it successfully (additive tables/indexes/constraints). No .env changes,
organization creation, ownership assignment or membership provisioning was performed.

Used the user's already-running Brave localhost app. Organizations navigation rendered;
pre-migration request showed retry instead of false no-membership. After migration, Retry
showed “No organization access yet” with working account link; desktop screenshot inspected.
Returned the tab to its original /app/account. No server started/stopped and no logout.
Browser checks of populated organization cards/settings, mobile layout, dark theme and
membership mutations were not executed. Relevant component and backend checks are E2/E3;
they are not described as full end-to-end browser proof.

## Review and limitations
Code review: skipped (ce-code-review unavailable) — the skill's required Git base cannot
be resolved because this workspace is not a functioning Git repository. No independent
review receipt is claimed. Manual source review covered actor/scope revalidation, row-lock
order, version checks, generated contracts, default-deny policy and stale UI requests.
Manual simplification retained the shared page helper, DTO projection and keyed read hook;
no security guard or proof test was removed.

General membership read/manage stays denied until 0004 wires its policy; owner transfer
API is reserved and implemented, with no transfer UI yet. Operator provisioning uses
API or management command. Admin registrations are read-only to avoid mutation bypass.
Historical worker/time/billing entities do not exist yet; tests prove stable membership
and event identity, not a future billing/report integration. Global user deactivation and
ORM/SQL administration are outside membership-command invariants; see design resolutions.
D-012 workload measurements and D-013 production audit retention remain open. No production
readiness claim, Git commit, PR, dependency install or background service was made.


## 0004 integration follow-up — 2026-10-18

The owner approved 0004 in full and requested completion of 0003 afterward. Its live
permission policy now governs member reads/add/status commands. Organization settings
include member addition by existing exact username, suspend/end/reactivate, and owner
transfer with reason/version checks. Stable membership identities and historical events
remain unchanged. No implicit organization or role grants were seeded. Non-owner managers
cannot change an owner's membership status. CLI provisioning accepts operator/owner UUIDs
or exact usernames. See [0004 verification](../0004-roles-permissions/verification.md) for
this follow-up's tests, UI checks and limits; earlier implementation limits are historical.


## User-guide follow-up — 2026-10-18

Owner requested configuration/examples and mandatory guide delivery. The [user guide](../../user-guide/README.md) now covers this feature in `organizations`. [Guide verification](../../user-guide/verification.md) records content/interaction/build checks and the unverified browser visual pass. This follow-up does not change prior implementation evidence or imply owner acceptance.
