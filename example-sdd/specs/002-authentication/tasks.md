# Task Breakdown — Authentication (Microsoft Entra ID SSO)

> **Purpose:** small, ordered, verifiable tasks that implement `plan.md`. Written at the owner's request in the same pass as the spec and plan. **Approved by the owner 2026-10-11 (amendment A-1 2026-10-13); implementation authorised separately (D-6); feature closed 2026-10-13.** Originally blocked until the spec's OPEN questions were resolved and spec and plan approved (all done).

## Conventions
- `[ ]` pending, `[x]` done, `[~]` in progress, `[!]` blocked. Order = execution order. Each task cites the plan section and spec items.
- Backend commands: `.\.venv\Scripts\python.exe manage.py check|test accounts|test core` from `backend\`. Frontend: `npm run lint|typecheck|test|build` from `frontend\`.
- No `.env` file is read or edited by the agent. Owner-only steps are marked **[Owner]**.

## Preconditions
- [!] **T0 — [Owner] Resolve OQ-1 to OQ-8 and approve spec and plan; register the Entra app** _(depends on: none)_
  - Implements: Spec §10, Plan §6
  - Done when: spec and plan are Approved; the owner has created the app registration (redirect URI `<APP_ORIGIN>/auth/callback`, "Assignment required"), and placed `MICROSOFT_*`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `AUTH_*`, and the frontend `APP_ORIGIN` values in the local `.env` files. Automated tests do not need them; manual validation does.

## Backend foundation
- [x] **T1 — Harden settings and add the `accounts` app skeleton** _(depends on: T0)_
  - Implements: Plan §2, §5 (foundation hardening, OQ-6), Spec AC-3.5
  - Done when: `SECRET_KEY`, `DEBUG` (default False), `ALLOWED_HOSTS`, session lifetimes and `MICROSOFT_*` are read from the environment; no key in source; `accounts` is in `INSTALLED_APPS`; DRF defaults set (session-header authentication, `IsAuthenticated`, error handler); `.env.example` lists the new names without values; `manage.py check` passes.
- [x] **T2 — Error envelope and request id** _(depends on: T1)_
  - Implements: Plan §5 (D-11)
  - Done when: a single exception handler returns the documented envelope with `request_id`; tests show 400/401/403/5xx shapes with no internals.
- [x] **T3 — Models and migration** _(depends on: T1)_
  - Implements: Plan §3, Spec AC-4.1, AC-8.1
  - Done when: `EntraIdentity`, `LoginAttempt`, `AuthEvent` exist with the specified constraints and one initial migration applies cleanly on PostgreSQL.
- [x] **T4 — Safe-redirect and attempt helpers** _(depends on: T3)_
  - Implements: Plan §5, Spec AC-2.3, AC-1.4
  - Done when: `next` sanitiser table tests pass (external URL, `//host`, backslash, scheme, control characters, long, `/login`, `/auth/*`); attempt creation hashes state and binding; expiry, single use and constant-time binding comparison are tested.

## External adapter
- [x] **T5 — Entra adapter** _(depends on: T1)_
  - Implements: Plan §6, Spec AC-1.2, AC-1.3, AC-1.5, AC-4.5
  - Done when: authorization URL (PKCE S256, nonce, state, `prompt=select_account`), discovery/JWKS caching, token exchange and ID-token validation work; tests with a generated RSA key and mocked `requests` cover valid, bad signature, wrong `aud`/`iss`/`tid`, expired, wrong nonce, missing `oid`, `alg=none`, timeout and 5xx; group/role claims are not read.

## Services and API
- [x] **T6 — Services: start, complete, end session, me, role assignment, audit** _(depends on: T3, T4, T5)_
  - Implements: Plan §2, §3, §5, Spec US-1, US-4, US-5, US-8
  - Done when: `complete_login` is atomic; identity keyed by `(tid, oid)` (changed or duplicate email tests); first sign-in creates a zero-role user; inactive user refused; audit written without secrets and failing audit fails sign-in closed; all service tests pass.
- [x] **T7 — Session authentication and permissions** _(depends on: T6)_
  - Implements: Plan §5, Spec AC-3.x, AC-5.x, AC-4.4
  - Done when: `SessionHeaderAuthentication` enforces idle (30 min) and absolute (8 h) lifetimes, rejects flushed and inactive-user sessions on the next request, and `IsSuperuser` / `HasRole` exist; role removal takes effect on the next request (tests).
- [x] **T8 — Accounts API endpoints** _(depends on: T2, T6, T7)_
  - Implements: Plan §4
  - Done when: `login/start`, `login/complete`, `me`, `logout` behave exactly per the contract including errors, uniform `invalid_attempt`, `Cache-Control: no-store`, and `/api/v1/accounts/` is routed in `config/urls.py`.
- [x] **T9 — Protect existing endpoints** _(depends on: T7)_
  - Implements: Plan §4 (existing endpoints), Spec AC-3.2, AC-3.5
  - Done when: `health` is explicitly public and unchanged; `system-info` returns 401 unauthenticated, 403 for non-superusers, 200 for superusers; a test enumerates all URL patterns and fails on any unlisted public endpoint.
- [x] **T10 — Operator role command** _(depends on: T6)_
  - Implements: Plan §2, Spec AC-4.7, AC-8.1
  - Done when: `manage.py assign_role` adds or removes a group for a user identified by object id or email, creates the group on demand, audits the change, and fails clearly for unknown users; tested.

## Frontend
- [x] **T11 — Read Next.js docs and extend the shared API client** _(depends on: T8)_
  - Implements: Plan §7, `docs/frontend-api-client.md` §3–4
  - Done when: `apiRequest` supports method, JSON body, session forwarding and envelope mapping; `getHealth` behaviour and all existing `api-client` tests are unchanged and passing; `lib/api/accounts.ts` is typed and tested against mocked responses.
- [x] **T12 — Auth helpers** _(depends on: T11)_
  - Implements: Plan §5, §7, Spec AC-2.3, AC-5.3, AC-6.3
  - Done when: `lib/auth/` provides the safe-redirect function (same cases as T4), cookie option builder (HttpOnly, SameSite=Lax, Secure outside development), Origin/Sec-Fetch-Site check, `getCurrentUser` and `requireUser`; unit tests pass; the module is `server-only`.
- [x] **T13 — BFF route handlers and `proxy.ts`** _(depends on: T12)_
  - Implements: Plan §7 (BFF), Spec US-1, US-2, US-6, US-7
  - Done when: `/auth/login`, `/auth/callback`, `/auth/logout` behave per the plan table (binding cookie, session cookie, safe redirect, error mapping to `/login?error=`, logout Origin check, 401-on-logout treated as success); `proxy.ts` redirects cookie-less requests to `/login?next=` and excludes `_next`, static, `/login`, `/auth/*`; the BFF register in `docs/architecture.md` §3 lists the three handlers (this docs change needs approval with the plan).
- [x] **T14 — Login page** _(depends on: T12)_
  - Implements: Plan §7, Spec AC-1.1, AC-2.4, AC-5.2, AC-6.1, AC-7.1–7.4
  - Done when: `/login` renders without the shell, matches the approved preview's look, has the single Microsoft action, shows each notice/error message accessibly (role/alert, keyboard operable, light and dark), redirects signed-in users, and never shows technical details.
- [x] **T15 — App Shell identity and logout** _(depends on: T12, T14)_
  - Implements: Plan §7, Spec AC-2.5, AC-6.1
  - Done when: the root layout resolves the user only when the cookie exists; `ProfileMenu` shows name and email and a working "Log out" form; the sidebar uses roles/permissions as a display hint only; `app/page.tsx` calls `requireUser()`; the shell tests still pass.

## Tests and validation
- [x] **T16 — Acceptance-criteria test sweep** _(depends on: T1–T15)_
  - Implements: Plan §10
  - Done when: every AC has an automated test where feasible; `manage.py check`, `manage.py test accounts core`, `npm run lint`, `typecheck`, `test` and `build` all pass with results recorded; criteria needing a real Entra tenant are listed as manual.
- [x] **T17 — Dependency housekeeping (only if OQ-7 approved)** _(depends on: T16)_
  - Implements: Plan §8, `docs/tech-stack.md`, D-18
  - Done when: `django-allauth`, `djangorestframework_simplejwt` and `oauthlib` are removed from `backend/requirements.txt` with checks still passing, and `docs/tech-stack.md` and `docs/decisions.md` (D-18, D-20, D-21, D-27) are updated to match the approved outcome. No package is installed.
- [x] **T18 (closed with limitations 2026-10-13; partly executed: sign-in and logout run, other manual checks not executed, see `validation.md` §6) — [Owner] Manual Entra verification** _(depends on: T0, T16)_
  - Implements: Spec AC-1.x, 2.x, 5.x, 6.x, 7.1–7.3
  - Done when: the owner runs the sign-in, chooser, deep-link, wrong-tenant, logout/back, timeout and role-command checks and the results are recorded (executed or not executed).
- [x] **T19 — Validation pass** _(depends on: T16, T18)_
  - Produces: `specs/002-authentication/validation.md` (planned and executed results separate; approved by the owner 2026-10-13)
  - Done when: every AC is Passed with executed evidence or explicitly Deferred or Not executed with a reason; `specs/README.md` updated.

## Amendment A-1 tasks (APPROVED 2026-10-13, implemented T20–T26)
Adopt the existing Entra redirect URI `<APP_ORIGIN>/api/auth/callback/azure-ad` (plan §14). No Auth.js/NextAuth/MSAL, no new dependency, no Entra change. T0 and T13 are read as amended: wherever they name `/auth/callback`, read `AUTH_CALLBACK_PATH` (`/api/auth/callback/azure-ad`).

- [x] **T20 — Single callback path constant** _(depends on: approval of A-1)_
  - Implements: Plan §14.2 items 1, 3, Spec AC-1.6
  - Done when: `frontend/lib/auth/paths.ts` exports `AUTH_CALLBACK_PATH`; `cookies.ts` sets `LOGIN_COOKIE_PATH = AUTH_CALLBACK_PATH`; no other source file contains the callback path literal (grep check in the validation record).
- [x] **T21 — Move the callback handler** _(depends on: T20)_
  - Implements: Plan §14.2 item 2, AC-1.6
  - Done when: `app/api/auth/callback/azure-ad/route.ts` exports `GET` only and calls `handleCallback`; `app/auth/callback/` no longer exists; the file-existence test passes.
- [x] **T22 — Proxy exact-path exemption** _(depends on: T20)_
  - Implements: Plan §14.2 item 4, AC-1.6, AC-3.1
  - Done when: a cookie-less request to exactly `AUTH_CALLBACK_PATH` passes through; any other path (including `/api/auth/other` and sub-paths of the callback) with no cookie is still redirected to `/login`; matcher unchanged.
- [x] **T23 — Redirect-URI drift guard and `next` sanitiser** _(depends on: T20)_
  - Implements: Plan §14.2 items 5, 6, AC-1.6, AC-2.3
  - Done when: `handleLoginStart` fails closed (`/login?error=unavailable`, no cookie, secret-free log) when Django's `redirect_uri` differs from `APP_ORIGIN + AUTH_CALLBACK_PATH`; `safeNextPath` (TS) and `safe_next_path` (Python) refuse `next` beginning with `/api/auth`; table tests updated in both.
- [x] **T24 — Tests, fixtures and docs wording** _(depends on: T21, T22, T23)_
  - Implements: Plan §14.4, §14.5
  - Done when: `tests/auth.test.mjs` and `accounts/tests/helpers.py` use the new URI; the plan §14.4 tests exist and pass; `.env.example` comments name the new URI; after the owner approves it, `docs/architecture.md` §3 BFF register row is renamed to `GET /api/auth/callback/azure-ad`.
- [x] **T25 — Automated validation and live smoke (agent)** _(depends on: T24)_
  - Implements: Plan §14.4
  - Done when: `manage.py check`, `manage.py test accounts core`, `npm run lint`, `typecheck`, `test`, `build` pass; the curl smoke (cookie-less callback → `/login?error=invalid`; with binding cookie → reaches Django and writes an audit event; old `/auth/callback` → 404) is recorded in `validation.md` as executed. The agent does not restart your servers: it will say when a restart is needed.
- [x] **T26 — [Owner] Live Entra sign-in** _(depends on: T25)_
  - Implements: Spec AC-1.2, AC-1.6, AC-2.1, AC-2.2
  - Done when: the owner signs in through Microsoft, lands on the home page, the audit log shows `login_succeeded`, and the result is recorded in `validation.md` (executed or not executed). Owner restarts Django (env unchanged) and Next.js (route moved).

## Notes
- Do not add tasks outside the approved plan; raise them for approval.
- Out of scope here: user-management UI, Graph, group sync, rate limiting, admin-site login, `/ui-preview/login` changes.

> Feature closed 2026-10-13. The Partial and Not-executed manual checks and the idle-expiry audit gap are recorded as limitations in `validation.md` §6 and are not marked passed. Changes outside these tasks that the owner reviewed are listed in `validation.md` §5.

## Change Log
| Date | Change | Reason | Approved by |
|---|---|---|---|
| 2026-10-13 | **Amendment A-1:** added T20–T26; T0 and T13 read with `AUTH_CALLBACK_PATH` instead of `/auth/callback`. | Existing Entra URI `/api/auth/callback/azure-ad` cannot change | Project owner, 2026-10-13 |
| 2026-10-13 | T18 and T19 closed (T18 with limitations); feature closed. Reviewed out-of-scope changes recorded in `validation.md` §5 (profile-menu logout fix, login-page Suspense, sidebar curve CSS, `gate.ts`). No tasks added. | Validation approved by the owner | Project owner, 2026-10-13 |

---
**Status:** Approved · **Feature closed:** 2026-10-13 · **Approved by:** Project owner · **Date:** 2026-10-13 · **Implementation of T0–T19 authorised:** Yes (2026-10-11) · **Implementation of A-1 (T20–T26) authorised:** Yes (2026-10-13); T20–T26 done
