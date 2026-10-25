# Verification — 0004 Roles & Permissions and 0003 integration

Status: Implemented and locally verified within approved scope; owner acceptance of the result pending.
Date: 2026-10-18. Authority: owner fully approved 0004 and requested implementation plus 0003 completion.

## Acceptance evidence

| Requirement | Executed evidence | Result |
| --- | --- | --- |
| AC-01 default deny, no staff bypass | `test_live_grant_revoke_and_default_deny`; existing organization scope tests; UI basic-member test | Passed |
| AC-02 known keys and tenant boundaries | `test_delegation_scope_and_strict_validation`: reserved/unknown keys, forged fields, foreign member/role, duplicate name and bounded queries | Passed |
| AC-03 live revocation | Grant/revoke then replay member GET with same authenticated user; frontend focus revalidation clears old private content | Passed |
| AC-04 delegation ceiling | Worker cannot self-grant or edit/archive a higher-powered role; ownership key rejected | Passed |
| AC-05 archive/suspension/history | Archive/restore and suspend/reactivate suppress/restore grants; same assignment remains, events retained | Passed |
| AC-06 self-summary | Exact worker permission set, inaccessible organization denial, basic-member UI avoids protected list fetches | Passed |
| AC-07 atomic conflict | Two concurrent PostgreSQL role edits produce one success and one 409, one complete key set; audit failure rolls back role creation | Passed |
| AC-08 project context | Missing resolver, missing/forged context denied; trusted resolver fixture grants matching active project role; mismatched project, org-only key and archived role denied | Passed for the interface; production projects resolver belongs to 0008 |
| 0003 follow-up | Existing membership/owner/history/concurrency regressions; real policy, exact username add, UI suspend conflict and ownership confirmation; CLI operator boundary | Passed |

The first new role test failed with expected 404 before implementation. The final suite uses
real PostgreSQL transactions, DRF endpoints and domain commands. Frontend tests mock only the
feature API boundary; they exercise rendered controls, submitted payloads, errors and refresh.
The project resolver test is explicitly a contract fixture, not evidence of a production project module.

## Commands and results

- PostgreSQL suite: `backend/.venv/bin/pytest -q -c backend/pyproject.toml backend/tests --tb=short`
  with the tracked local compose database URL as DATABASE_URL: **34 passed**. Uses isolated test DB.
- `npm run test --prefix frontend`: **20 passed**, 3 files.
- `backend/.venv/bin/ruff check backend scripts`: passed.
- `backend/.venv/bin/ruff format --check backend`: 97 files already formatted.
- `python3 scripts/check_boundaries.py`: passed.
- `python3 -m unittest discover -s scripts -p 'test_*.py'`: 3 passed.
- `manage.py check`: no issues; `makemigrations --check --dry-run`: no changes;
  `migrate --check`: no pending migrations on configured local DB.
- `manage.py spectacular --file docs/api/openapi.yaml --validate --fail-on-warn`: passed.
- `npm run api:types --prefix frontend`: generated types from validated schema.
- `npm run typecheck`, `npm run lint`, `npm run build` (frontend): passed.

The additive identity.0002 migration was reviewed with `migrate --plan` and applied to the
configured local DB. Existing organization migration rehearsal also exercises removal/reapply
of its dependent identity migration in the isolated test DB. No existing users were auto-enrolled;
no business roles, assignments, organizations or sample data were seeded in the configured DB.

## Browser checks

Used the user's existing frontend server; no backend/frontend server was started or stopped.
Verified real organization navigation and empty state with the existing logged-in session.
For owner controls, used a temporary, isolated Vite HTML fixture with in-memory API responses
and disabled mutations: desktop light role editor; mobile 390×844 dark role editor; keyboard
Tab focus and Escape close; measured document width/scrollWidth both 390. The fixture files
and temporary browser tab were removed, viewport reset, user tab restored to `/app/account`.
This verifies rendering/accessibility interactions, not live authenticated write wiring. Real
writes are covered by PostgreSQL API tests and API-boundary frontend interaction tests.

## Source review and simplification

Applied `ce-simplify-code` review of the edited source set: independent reuse, quality, efficiency, test-value and comment reviews preserved security
proof tests and public contract notes. Reused shared pagination/validation helpers and refresh callback, removed a
redundant tuple conversion, used the typed RoleUpdate alias, and avoided repeated post-write
role-permission queries for audit/response. Removed two implementation-summary docstrings.
Final checks above cover the behavior changes; the last import/docstring cleanup also
passed Ruff and Django system checks.

Code review: skipped (ce-code-review unavailable) — the required Git diff base cannot be
resolved because this workspace is not a functioning Git repository. The skill's scope stage
terminated there; no formal review receipt is claimed. A manual source scan covered live
permission checks, tenant filtering, delegation, optimistic versions, shared lock order,
event atomicity, generated APIs, UI action gating and stale-response cleanup. No blocking
issue remained. No Git commit or PR was created.

## Remaining scope limits

- 0008 owns real project scope resolution and project-role assignment. The composition port
  defaults to denial until that module registers its resolver.
- 0005–0008 and invitations/public signup remain unimplemented and unapproved.
- D-012 load targets/query-plan/p95 benchmarking and D-013 production retention/access policy
  remain open. These checks are not a capacity benchmark or production-readiness guarantee.
- Global Django-user deactivation is an operator action outside organization locking; operators
  must avoid disabling the sole owner without arranging recovery/transfer.
- Browser mutation flows against real accounts were not performed. User acceptance remains pending.


## UI/Admin follow-up — 2026-10-18

User clarified that creation and management must be accessible from both application UI
and Django Admin. New tests exercise actual admin POST forms for organization, membership,
role, assignment, revoke, suspension/reactivation and owner transfer. They assert history,
stale-version rejection, no superuser tenant bypass, and Admin CSRF rejection. Public API
tests cover capability visibility and exact owner username; frontend tests cover operator
creation and ordinary-member hidden action. Latest suite: **37 backend / 22 frontend**.
Typecheck, lint, production build, Django checks and boundary validation pass. No migration
needed. Existing live browser session verified both creation forms without submitting data.
A temporary Admin tab was closed; the app remains on Organizations. No server was started.
Earlier verification counts and read-only Admin notes describe the previous delivery.


## User-guide follow-up — 2026-10-18

Owner requested configuration/examples and mandatory guide delivery. The [user guide](../../user-guide/README.md) now covers this feature in `roles`. [Guide verification](../../user-guide/verification.md) records content/interaction/build checks and the unverified browser visual pass. This follow-up does not change prior implementation evidence or imply owner acceptance.

## Settings layout revalidation fix — 2026-10-18

Owner reported periodic page jumping. The organization read hook cleared its data
on every 60-second visible-tab refresh and window focus, unmounting Settings and
its access forms in favour of a short loading paragraph. Two new regression cases
first failed at the pending-refresh heading assertion (focus and timer).
Removed that eager clearing for same-mounted-scope refreshes. Successful responses
update the existing view; failures still remove private content. Organization/page
keys and cancellation/stale-response rejection remain unchanged. User guide #roles
now describes background revalidation. This changes no API permissions or interval.

A first fix also kept explicit mutation-conflict retries mounted, which left the
existing alert behind an open dialog; the conflict regression caught that failure.
Separated background refresh from explicit retry: focus/timer retain content while
manual/conflict retry clears its old snapshot as before. Final frontend suite:
48 passed (8 files), including both new pending-refresh regressions, tenant-switch
isolation, revoked access and the existing conflict/no-replay scenario. Lint passed.
