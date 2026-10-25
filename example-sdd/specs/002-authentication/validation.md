# Validation Record — Authentication (Microsoft Entra ID SSO)

> Feature `002-authentication`. Planned and executed validation are reported separately (P6). A criterion is **Passed** only with executed evidence. Criteria that need a real Entra tenant are **Not executed**.

## 1. Executed validation (2026-10-11)

| # | Command | Result |
|---|---|---|
| E1 | `manage.py check` (backend) | No issues |
| E2 | `manage.py makemigrations --check --dry-run` | No changes detected (initial `accounts` migration committed to the tree, **not applied** to the local database) |
| E3 | `manage.py test accounts core` (PostgreSQL test database) | 50 tests, OK |
| E4 | `npm test` (frontend) | 65 tests, 65 pass (includes the unchanged api-client, raw-colour, token and navigation suites) |
| E5 | `npm run lint` | No errors or warnings |
| E6 | `npm run typecheck` | No errors |
| E7 | `npm run build` (Next.js 16.4, Cache Components) | Succeeded. Routes: `/`, `/login`, `/auth/login`, `/auth/callback`, `/auth/logout`, Proxy |
| E8 | `next start` smoke test with Django stopped (curl) | `/` and `/reports?x=1` → 307 to `/login` and `/login?next=%2Freports%3Fx%3D1`; `/login` shows the Microsoft button; unknown `error` keys are not rendered; cross-site `POST /auth/logout` → 403; `/auth/login` with Django down → `/login?error=unavailable`; callback without binding cookie → `/login?error=invalid`; a bogus session cookie with Django down leaks no protected content |

### 1a. Re-run and live checks (2026-10-13)

| # | Command / check | Result |
|---|---|---|
| E9 | `manage.py check`, `makemigrations --check --dry-run`, `manage.py test accounts core` | No issues; no changes; 50 tests OK. `accounts` migration `0001_initial` is now applied to the local database |
| E10 | `npm run lint`, `npm run typecheck`, `npm test` | No errors; no errors; 65 of 65 pass. `npm run build` **not re-run** (a dev server was running; build output would clash) |
| E11 | Live `/auth/login` (curl, Django + Next dev running) | 302 to `login.microsoftonline.com/<tenant>/oauth2/v2.0/authorize` with `response_type=code`, `scope=openid profile email`, `state`, `nonce`, `code_challenge_method=S256`, `prompt=select_account`, `redirect_uri=http://localhost:3000/auth/callback`; `timely_login` cookie set (HttpOnly, SameSite=Lax, Path=/auth/callback, Max-Age=600). Microsoft served its sign-in page (no `AADSTS` code on load) |
| E12 | Callback with the binding cookie and a fake code (curl) | Reaches Django; refused as `not_completed`. Without the cookie: `invalid`. Both correct |
| E13 | Simulated post-login leg: a real Django session created in the shell (test user, removed afterwards) | Django `/me` → 200 with identity; frontend `/` → 200 with the cookie (no bounce to `/login`) |
| E14 | Owner's live sign-in attempt in a browser (typed `http://localhost:3000`) | **Failed.** Microsoft redirected back and the owner landed on `/login` with **no message**. Audit log after the attempt: one `login_started` (#32), **no** `login_refused` or `login_succeeded`, no new identity. `login/complete` was never called |
| E15 | Root-cause trace (2026-10-13, before the change) | Registered Entra URI = running `MICROSOFT_REDIRECT_URI` = runtime `redirect_uri` = `http://localhost:3000/api/auth/callback/azure-ad`. No Auth.js/NextAuth/MSAL in `package.json`, `node_modules` or source. Only `GET /auth/callback` was implemented. `GET /api/auth/callback/azure-ad?code=x&state=y` → `307 /login?next=…` (proxy redirect). This explains E14. Plan §14 |

### 1b. Amendment A-1 implementation (2026-10-13, tasks T20–T25)

| # | Command / check | Result |
|---|---|---|
| E16 | `npm test` | 68 of 68 pass (3 new: callback path/cookie path/file-existence, proxy gate exact-path, drift guard; `next` table extended) |
| E17 | `manage.py test accounts core` | 51 tests OK (new `next` cases for `/api/auth/*`; fixture URI aligned) |
| E18 | `npm run lint`, `npm run typecheck` | No errors |
| E19 | `npm run build` | Succeeded. Routes include `ƒ /api/auth/callback/azure-ad`, `/auth/login`, `/auth/logout`; `/auth/callback` is gone. The running dev server stayed up (`/login` 200) |
| E20 | Literal check | `/api/auth/callback/azure-ad` appears in one source file only (`lib/auth/paths.ts`); no callback path in backend source |
| E21 | Live smoke on the running dev server and Django (curl) | (1) cookie-less `GET` callback → `302 /login?error=invalid` (**not** `/login?next=…`); (2) old `/auth/callback` → `404`; (3) `/api/auth/other` cookie-less → `307 /login` (exemption is exact-path); (4) `/auth/login` → 302 to Entra, `redirect_uri=http://localhost:3000/api/auth/callback/azure-ad`, cookie `timely_login; Path=/api/auth/callback/azure-ad; HttpOnly; SameSite=Lax`; (5) callback with that cookie and a fake code → reaches Django and Django contacts Entra: `302 /login?error=not_completed`, audit event `login_refused token_rejected` (#37) |
| E22 | Owner live Microsoft sign-in (T26), reported by the owner and corroborated by the audit log | Owner reached the app shell. Audit log: `user_created` (#39), `login_succeeded` (#40, #45); one `EntraIdentity`; the user has **no roles**, is active and not a superuser |
| E23 | Logout in a real browser (headless Edge over CDP, temporary session, since deleted) | **Defect found and fixed:** the **Log out** menu item sent no request because Radix unmounted the button before the form submitted (reproduced: no `POST`, stays on `/`). Fix: `onSelect` is prevented in `components/shell/profile-menu.tsx`. After the fix: `POST /auth/logout` sent, redirect to `/login?notice=signed_out`, message shown. Also by curl: cross-site `POST` → 403; same-origin → 303, cookie cleared (`Max-Age=0`), the old key then returns 401 from `/me`, audit `logout` written |
| E24 | Sidebar rail curve hairline (feature 001 shell style, reported by the owner) | Reproduced in headless Edge at 125% and 175% display scale; fixed in `app/globals.css` (curves overlap the panel by 1px). Seam artefact count 9 → 0 at 125%/175%, 0 at 100%/150%/200%. Visual check of the curve shape. `npm test` 68/68, lint clean |

## 2. Acceptance criteria

Legend: **Passed** = executed automated evidence. **Partial** = backend/logic proven, browser or Entra behaviour not executed. **Not executed** = needs a real Entra app registration or a browser.

| AC | Status | Evidence / gap |
|---|---|---|
| AC-1.1 | Partial | E8: login page renders one Microsoft action and no password fields. Visual match to the preview not reviewed in a browser |
| AC-1.2 | Passed | E22 live Microsoft sign-in returned the owner to the app shell; audit `login_succeeded` #40, #45 (owner-reported, corroborated by audit). Also mocked Entra (E3 `test_successful_sign_in_*`, adapter tests) |
| AC-1.3 | Partial | E3 `test_authorization_url_has_pkce_state_nonce_and_account_choice` (`prompt=select_account`). Actual chooser not observed |
| AC-1.4 | Passed | E3: unknown, expired, reused and wrong-binding attempts refused (`test_attempt_is_single_use`, `test_wrong_binding_*`, `test_unknown_state_and_expired_attempt`); E4: callback without binding cookie never reaches Django |
| AC-1.5 | Passed | E3 `test_wrong_tenant_is_refused_and_audited`; adapter `test_rejections` |
| AC-1.6 (A-1) | Passed | E16 (path/cookie/file/gate/drift tests), E20, E21 (callback reached without a session, processed by Django, old route gone, one path constant plus env) and E22 (live sign-in through the registered URI succeeded) |
| AC-2.1 | Passed | E22: after Microsoft sign-in the owner landed on the app shell (home); E4 redirect to `/` |
| AC-2.2 | Partial | E3/E4: next stored, returned and followed (`/reports`). End-to-end deep link not executed |
| AC-2.3 | Passed | E3 `SafeNextPathTests`; E4 `safeNextPath` and hostile-`next` callback test |
| AC-2.4 | Not executed | Implemented in `app/login/page.tsx` (redirect when signed in); needs a signed-in browser |
| AC-2.5 | Partial | `/me/` returns name, email, roles, permissions (E3). Shell/menu rendering and navigation hint not executed in a browser; no permission-gated nav entries exist yet |
| AC-3.1 | Partial | E8: unauthenticated page requests redirect with `next`. `requireUser()` redirect path not executed with a live Django |
| AC-3.2 | Passed | E3 `test_every_api_endpoint_requires_authentication_unless_listed` |
| AC-3.3 | Passed | E3 `test_system_info_is_restricted_to_superusers` (403 for signed-in non-superuser); `HasRole` provided for later features (not yet exercised by an endpoint) |
| AC-3.4 | Passed | E3 `test_cookie_is_not_an_accepted_credential`, `test_group_and_role_claims_are_not_read` |
| AC-3.5 | Passed | E3 URL-enumeration test (public set equals health, login start, login complete); `/login`, `/auth/*` are the only public pages (E8) |
| AC-3.6 | Passed | E3 `test_deactivation_applies_on_next_request` |
| AC-4.1 | Passed | E3 `test_identity_is_keyed_by_object_id_not_email`, `test_pre_existing_local_user_with_same_email_is_not_linked` |
| AC-4.2 | Passed | E3 `test_successful_sign_in_creates_zero_role_user`; E22 live: `user_created` #39, the new user has no roles |
| AC-4.3 | Passed | E3 `test_second_sign_in_reuses_user_and_refreshes_profile` |
| AC-4.4 | Passed | E3 `test_role_assignment_applies_on_next_request` |
| AC-4.5 | Passed | Adapter ignores `groups`/`roles` claims (E3) |
| AC-4.6 | Passed | E3 `test_me_returns_own_identity_only` (no id in response, no id parameter) |
| AC-4.7 | Passed | E3 `AssignRoleCommandTests` (assign, remove, unknown, ambiguous) |
| AC-5.1 | Passed | E3 `test_absolute_lifetime`, `test_idle_expiry`, `test_idle_expiry_slides_but_is_capped_by_absolute` |
| AC-5.2 | Partial | `session_expired` code and `/login?notice=session_ended` implemented; message mapping tested (E4). Browser flow not executed |
| AC-5.3 | Partial | E4 cookie attributes (HttpOnly, SameSite=Lax, Secure on https); no browser-storage use in code. Browser inspection not executed |
| AC-5.4 | Passed | No Microsoft token persisted (models hold no token fields; E3 `test_token_is_not_stored_*`); `offline_access` not requested |
| AC-5.5 | Passed | E3 `test_logout_ends_session_and_is_audited` |
| AC-6.1 | Passed | E23: menu click in a real browser sends `POST /auth/logout`, clears the cookie, lands on `/login?notice=signed_out` with the message (after fixing the menu-item defect); E3 session flushed, `logout` audited |
| AC-6.2 | Partial | E3 and E23: the old key returns 401 after logout. Browser back button not executed |
| AC-6.3 | Passed | E4 cross-site logout refused without calling Django; E8 live 403 |
| AC-6.4 | Passed | By design: logout only ends the Timely session (E3/E4). No Entra end-session call exists |
| AC-7.1 | Passed | E3 502 `idp_unavailable`; E4 and E8 `unavailable` message |
| AC-7.2 | Passed | E3 `test_idp_error_consumes_attempt`; E4 `not_completed` mapping |
| AC-7.3 | Passed | E3 inactive refusal; E4 `no_access` mapping. Contact text is "contact your administrator" (OQ-8 default) |
| AC-7.4 | Passed | E3 uniform error envelope, no internals; E4 only known message keys rendered (E8 injection check) |
| AC-7.5 | Partial | E8: no protected content when Django is down. The error boundary's visible "unavailable" state was not observed in a browser |
| AC-8.1 | Partial | E3: login_started, login_succeeded, login_refused, user_created, logout, session_expired (absolute), access_refused_inactive, role_assigned/removed recorded. **Gap:** idle-timeout expiry cannot be attributed to a user and is not audited |
| AC-8.2 | Passed | E3 `test_token_is_not_stored_and_events_hold_no_secrets` |

## 3. Planned validation (not executed)

Remaining manual checks (needs the owner's Entra app and a browser, task T18). **Executed:** sign-in, first-time user creation, logout (E22, E23). **Not executed:** account chooser observed, deep-link return through Microsoft, wrong-tenant and guest accounts, "Assignment required" refusal, browser back button after logout, idle and absolute timeout in the browser, role assignment via `manage.py assign_role` then `/me` shown in the shell, light/dark and keyboard check of `/login`, and the visible "unavailable" error state.

Owner setup before manual checks (T0, as amended by A-1): the Entra app is registered with redirect URI `<APP_ORIGIN>/api/auth/callback/azure-ad` (unchanged); `SECRET_KEY`, `MICROSOFT_*` (with `MICROSOFT_REDIRECT_URI` equal to that URI), `ALLOWED_HOSTS` in `backend\.env`, `APP_ORIGIN` in `frontend\.env.local` and `manage.py migrate` are done.

Amendment A-1 planned checks (plan §14.4) were **executed**: see E16–E22.

## 4. Deviations, limitations and notes

- **RESOLVED (2026-10-13):** the registered Entra URI `…/api/auth/callback/azure-ad` had no route (E15). Amendment A-1 (approved 2026-10-13) moved the callback to that path (E16–E21) and the owner's live sign-in succeeded (E22). AC-2.2 (deep link through Microsoft) remains Partial.
- **Defects found and fixed during manual validation (not in the approved tasks, flag for review):** (1) the profile-menu **Log out** item did nothing (E23, `components/shell/profile-menu.tsx`); (2) a hairline on the sidebar rail curves at fractional display scales (E24, `app/globals.css`, a feature 001 shell style, so feature 001's validation does not list it).
- **Implementation notes for review (A-1):** the proxy decision was extracted to a pure `lib/auth/gate.ts` (not named in the plan; needed to unit-test the exact-path exemption without the Next runtime); `proxy.ts` now delegates to it with an unchanged matcher. `docs/architecture.md` BFF register row and `backend/.env.example` comments were updated. `backend` source has no change (only a test fixture and the `next` sanitiser).
- **Setup note (A-1):** the owner's Entra registration is `<APP_ORIGIN>/api/auth/callback/azure-ad` and cannot be changed. `MICROSOFT_REDIRECT_URI` must equal it (it already does) and must be registered under the **Web** platform; the Next.js server must be restarted after editing `frontend\.env.local` or moving routes, Django after editing `backend\.env`. Earlier notes that named `/auth/callback` as the value to register are superseded.
- **Change made during validation:** `app/login/page.tsx` now reads `searchParams` and the session inside a `<Suspense>` boundary (removes the Next.js 16 "URL data during prerendering" dev error). Lint, typecheck and tests pass. Needs owner review as it was not in the approved tasks. `backend/.env.example` and `frontend/.env.example` gained explanatory comments (no values).
- **Existing behaviour changed (approved in spec AC-3.5/OQ-6):** `system-info` now needs a superuser; `SECRET_KEY` is required from the environment (the app will not start without it); `DEBUG` defaults to False.
- `tsconfig.json` gained `allowImportingTsExtensions` so the auth modules can be unit-tested with `node --test` (same pattern as existing tests). Not listed in the plan; flag for review.
- Root layout now resolves the user at request time behind a `Suspense` boundary (Cache Components). `/login` and the authenticated pages are partially prerendered with dynamic content streamed.
- The existing `/ui-preview` pages now require sign-in (deny by default). `/ui-preview/login` is unchanged.
- If Django is unreachable at logout, the browser cookie is cleared but the Django session lives until it times out (logged, not hidden).
- Audit gap: idle-expiry events (see AC-8.1). Rate limiting, audit retention and Graph-based revocation remain DEFERRED as specified.
- `requirements.txt` no longer lists `django-allauth`, `djangorestframework_simplejwt` or `oauthlib`; no package was installed or uninstalled in the environment.
- Docs updated: `architecture.md` (BFF register, foundation gaps), `decisions.md` (D-55 to D-58), `tech-stack.md`, `frontend-ui-rules.md`. The two PROPOSED conventions D-11 (error envelope) and D-12 (URL scheme) were used as written.
- The Django admin site still uses its own password login (out of scope, risk R-7).

## 5. Reviewed changes outside the approved tasks
The owner reviewed these during validation and accepted them with the validation approval of 2026-10-13. Each is small, was verified (see the evidence column), and adds no feature.

| # | Change | File(s) | Why | Evidence |
|---|---|---|---|---|
| 1 | Profile-menu **Log out** item no longer unmounts before the form submits (`onSelect` prevented) | `frontend/components/shell/profile-menu.tsx` | The button did nothing: Radix removed it before the browser submitted the form (AC-6.1) | E23: reproduced without the fix, passes with it; lint, typecheck, tests |
| 2 | `/login` reads `searchParams` and the session inside a `<Suspense>` boundary | `frontend/app/login/page.tsx` | Removed the Next.js 16 "URL data during prerendering" dev error | Lint, typecheck, 68 tests; `/login` renders (§1a) |
| 3 | Sidebar rail curves overlap the panel by 1px | `frontend/app/globals.css` (feature 001 shell style) | A hairline appeared at fractional display scales (125%, 175%) | E24: artefact count 9 → 0 at 125%/175%; visual check |
| 4 | Pure proxy decision extracted to `lib/auth/gate.ts`; `proxy.ts` delegates to it (matcher unchanged) | `frontend/lib/auth/gate.ts`, `frontend/proxy.ts` | To unit-test the exact-path callback exemption (amendment A-1) without the Next runtime | E16 gate test; E21 live smoke |
| 5 | `tsconfig.json` `allowImportingTsExtensions` (from the original implementation) | `frontend/tsconfig.json` | Lets auth modules be tested with `node --test`, same pattern as existing tests | `npm test` |

Feature 001's validation records change 3 as a post-closure note.

## 6. Closure record and limitations (not passes)
**Closed 2026-10-13.** The owner approved this validation record on 2026-10-13 (message: approval of closing Feature 002 "based on the evidence recorded in `specs/002-authentication/validation.md`"). The feature is closed with the following limitations. None is marked Passed.

| Item | Status | Notes |
|---|---|---|
| AC-1.1 visual match to the preview | Partial | Renders one Microsoft action (E8); not reviewed against the preview in a browser |
| AC-1.3 account chooser | Partial | `prompt=select_account` is sent (E3, E11); the chooser was not observed |
| AC-2.2 deep link through Microsoft | Partial | `next` is stored, returned and followed (E3/E4); not run end to end |
| AC-2.4 signed-in user opening `/login` | Not executed | Implemented in `app/login/page.tsx`; not run in a signed-in browser |
| AC-2.5 shell and menu rendering | Partial | `/me` returns name, email, roles, permissions (E3); no permission-gated navigation entries exist yet |
| AC-3.1 `requireUser()` redirect | Partial | Cookie-less redirect proven (E8); the `requireUser()` path not run with a live Django |
| AC-5.2 session-ended notice in a browser | Partial | Code and message mapping tested (E4); browser flow not executed |
| AC-5.3 cookie attributes in a browser | Partial | Attributes proven in tests (E4) and curl (E11, E21); browser storage not inspected |
| AC-6.2 back button after logout | Partial | Old key refused (E3, E23); back button not executed |
| AC-7.5 visible "unavailable" boundary | Partial | No protected content when Django is down (E8); the visible state was not observed |
| AC-8.1 idle-expiry audit | **Gap** | Idle-timeout expiry cannot be attributed to a user and is **not audited**. Absolute expiry and all other listed events are audited. Not fixed in this feature (no scope expansion); candidate for a later feature |
| Wrong-tenant and guest accounts, "Assignment required" refusal in a real tenant | Not executed | Wrong-tenant refusal is proven with a mocked Entra (AC-1.5) |
| Idle and absolute timeout in a browser; `assign_role` shown in the shell; light/dark and keyboard check of `/login` | Not executed | Backend behaviour proven (AC-5.1, AC-4.4, AC-4.7) |
| `.env` comment at `backend/.env` line 17 | Note | The comment still names the old path; `MICROSOFT_REDIRECT_URI` (line 20) is correct. Cosmetic, owner's file |

Still **DEFERRED** as specified: rate limiting, audit retention, Graph-based revocation. Not part of this feature: user-management UI, the Django admin login, the token-based mobile/microservice design (discussed only; would need a new feature and spec amendment).

## 7. Change Log
| Date | Change | Reason | Approved by |
|---|---|---|---|
| 2026-10-13 | Re-run, live checks, amendment A-1 evidence (§1a, §1b), defects fixed, reviewed changes (§5), limitations (§6) | Owner manual validation | Project owner |
| 2026-10-13 | Validation approved and Feature 002 closed with the limitations in §6 | Owner approval message of 2026-10-13 | Project owner |

---
**Status:** Approved · **Approved by:** Project owner · **Date:** 2026-10-13 · **Feature closed:** 2026-10-13 · **Implementation authorised:** Yes (2026-10-11; A-1 2026-10-13) · **Manual items:** Partial or Not executed, listed in §6
