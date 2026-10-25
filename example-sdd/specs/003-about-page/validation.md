# Validation Record — About Page

> **Purpose:** prove each acceptance criterion in `spec.md` is met. A requirement is **Passed** only when its test or validation was executed and the result recorded (P6). Planned and executed validation are reported separately.
> **Location:** `specs/003-about-page/validation.md`.

## 1. Planned Validation
| Spec ID | Planned test / check |
|---|---|
| AC-1.1 | `about/tests/test_about.py::ApiTests.test_about_for_user_with_no_roles`; `ServiceTests` |
| AC-1.2 | Manual: no-logo placeholder on About (default mark); `tests/about.test.mjs::resolveBrand…` |
| AC-2.1, 2.3 | `ServiceTests.test_ordering_and_empty_group_omitted`; `SeedTests` |
| AC-2.2 | Seed data carries "Ex." in designation text (`SeedTests`); no extra mechanism |
| AC-3.1 | `ApiTests.test_about_for_user_with_no_roles` (acknowledgement fields) |
| AC-3.2 | `ServiceTests.test_unsafe_stored_url_is_omitted`, `test_model_rejects_non_http_url`; link attributes by code review and manual |
| AC-4.1 | Manual (empty note hides block); `about/page.tsx` conditional |
| AC-5.1 | `AdminTests.test_edit_shows_in_api_and_writes_history` |
| AC-5.2 | `AdminTests.test_non_staff_and_staff_without_permission_cannot_edit`; `test_singleton_cannot_be_added_or_deleted` |
| AC-5.3 | `SeedTests` |
| AC-5.4 | `AdminTests.test_edit_shows_in_api_and_writes_history`, `test_bad_uploads_are_rejected`, `ImageValidationTests` |
| AC-6.1 | `tests/about.test.mjs` (navigation + profile menu link); manual |
| AC-7.1 | `ApiTests.test_identity_is_public_and_minimal`; `tests/about.test.mjs::getBrand…`; manual smoke |
| AC-7.2 | Manual visual check of each surface |
| AC-7.3 | `tests/about.test.mjs::getBrand falls back…`; manual (backend stopped) |
| AC-7.4 | `ApiTests` (public endpoints, minimal payload); `accounts/tests/test_security.py::DenyByDefaultTests`; `tests/auth.test.mjs` gate test |
| AC-X.1 | `ApiTests.test_about_requires_sign_in`; `DenyByDefaultTests` |
| AC-X.2 | Shared error boundary (`app/error.tsx`); manual (backend stopped) |
| AC-X.3 | `ServiceTests.test_empty_database_does_not_fail` |
| AC-X.4 | Manual: responsive, keyboard, theme |

## 2. Executed Validation
Date: 2026-10-13. Windows, local PostgreSQL, Python 3.14.5, Node 24.

Commands run:
- `manage.py makemigrations --check --dry-run` → no changes.
- `manage.py test about accounts core --noinput` → **73 tests, OK** (includes the updated deny-by-default list in `accounts/tests/test_security.py`).
- `npm test` → **78 tests, 78 pass, 0 fail**.
- `npm run lint` → clean. `npm run typecheck` → clean. `npm run build` → success (`/about`, `/brand/logo`, `/brand/favicon` present).
- Manual smoke with `manage.py migrate about`, `runserver` and `npm run start`, using `curl`:

| Spec ID | Test / check | Result | Evidence / notes |
|---|---|---|---|
| AC-1.1 | `ApiTests.test_about_for_user_with_no_roles`, `ServiceTests` | Passed | Authenticated user without roles gets full payload with the specified fields. |
| AC-1.2 | `resolveBrand` unit test (no logo → default mark). Visual check on About page | Partial | Logic tested; About page not viewed in a browser. |
| AC-2.1 | `ServiceTests.test_ordering_and_empty_group_omitted` | Passed | |
| AC-2.2 | `SeedTests` | Passed | "(Ex.)" kept in designation text; no extra mechanism. |
| AC-2.3 | `ServiceTests.test_ordering_and_empty_group_omitted` | Passed | |
| AC-3.1 | `ApiTests.test_about_for_user_with_no_roles` | Passed | Fields `name, used_for, attribution_text, url`. |
| AC-3.2 | `ServiceTests.test_unsafe_stored_url_is_omitted`, `test_model_rejects_non_http_url` | Partial | http/https enforced and tested. `target="_blank" rel="noopener noreferrer"` verified by code only, not rendered in a browser. |
| AC-4.1 | Code (`about.special_thanks && …`) | Partial | Not browser-verified. |
| AC-5.1 | `AdminTests.test_edit_shows_in_api_and_writes_history` | Passed | |
| AC-5.2 | `AdminTests` permission and singleton tests | Passed | Non-staff redirected, staff without permission 403, add/delete of singleton 403. |
| AC-5.3 | `SeedTests` (7 groups, 12 people, OpenStreetMap, 1 identity, idempotent) | Passed | Also applied to the local dev DB with `migrate about`. |
| AC-5.4 | `AdminTests.test_bad_uploads_are_rejected`, `ImageValidationTests` | Passed | SVG, wrong type, mismatched content, oversize rejected; version is a free text field. Real upload through the admin page in a browser: Not executed (upload exercised through the test client only). |
| AC-6.1 | `tests/about.test.mjs` (nav item and profile-menu link) | Partial | Menu visibility in a browser Not executed. |
| AC-7.1 | `ApiTests`, `getBrand` tests, and smoke: after setting a logo and favicon, `/login` HTML contained `<link rel="icon" href="/brand/favicon?v=…">` and `<img src="/brand/logo?v=…">`; `/brand/logo` returned 200 `image/png`, `nosniff`, `immutable` | Passed (login page); Partial (shell surfaces) | Sidebar, header, drawer and footer use the same provider but were not viewed in a browser. |
| AC-7.2 | Code review of surfaces (rail, header, drawer, sign-in, tab title/favicon). Footer text uses the name only through the same `useBrand()` (footer still reads the shell's brand) | Partial | Not visually confirmed. `ui-preview/login` (design prototype) keeps the default brand on purpose; it is not a real surface. |
| AC-7.3 | `getBrand falls back…` tests; smoke: Django stopped → `/login` 200 with title "Sign in \| Timely", `/brand/logo` 502 | Passed | |
| AC-7.4 | `ApiTests`, deny-by-default list, gate test; smoke: `/brand/logo` and `/brand/favicon` reachable without a session, `/about` redirects to `/login?next=%2Fabout` | Passed | |
| AC-X.1 | `ApiTests.test_about_requires_sign_in`, `DenyByDefaultTests`; smoke 401 and 307 | Passed | |
| AC-X.2 | `app/error.tsx` (existing boundary) | Not run | Not exercised on `/about` with the backend stopped while signed in (needs a real session). |
| AC-X.3 | `ServiceTests.test_empty_database_does_not_fail` | Passed | Empty-state UI Not viewed. |
| AC-X.4 | — | Not run | Responsive, keyboard and theme review not executed. Tokens only; `raw-colors` test passes. |

## 3. API-First Compliance
| Check | Result | Evidence |
|---|---|---|
| Endpoints match the plan's contract | Passed | `ApiTests` assert exact field sets, headers and status codes |
| Auth and permission cases incl. refusal | Passed | 401 unauthenticated; admin refusal tests; deny-by-default test lists exactly the three public About URLs |
| Server-side validation and error envelope | Passed | Image/URL validation tests; 401 uses the existing envelope. Public image 404 returns an empty body by design |
| Frontend uses only the shared API client | Passed | `lib/api/about.ts` uses `apiRequest`/`apiRequestBytes` from `lib/api/client.ts`; no other `fetch` added |
| No frontend DB or external system access | Passed | No DB driver or external call added |
| Route Handlers/BFF justified and registered | Passed | `GET /brand/logo`, `GET /brand/favicon` in `docs/architecture.md` §3 |
| External systems only through adapters | Passed | None used |
| No module reads another module's models | Passed | `about` imports nothing from `accounts` or `core` (tests import `accounts.tests.helpers` for sign-in only) |

## 4. Constitution Compliance
| Principle | Result | Evidence |
|---|---|---|
| P1 Spec first, gates | Passed | Spec, plan and tasks approved 2026-10-13; implementation separately authorised |
| P2 Decisions labelled | Passed | Plan §13 points accepted with plan approval; AC-7.2 / AC-7.4 / OQ-4 stay as approved proposals |
| P3 Modular monolith | Passed | New `about` module; structure still OPEN (D-22) |
| P4 Adapters | Passed | No external systems |
| P5 Security, privacy, audit | Passed with note | Server-side auth; minimal public data; admin history (`LogEntry`) tested; audit events remain OPEN (D-30) |
| P6 Evidence-based validation | Passed | This record separates executed from not executed |
| P7 Minimal footprint | Passed | No new dependency or infrastructure; no Docker/WSL; no AI |
| P8 API-first | Passed | See §3 |

## 5. Non-Functional Requirements
- Performance: one extra identity request per page render with a 5 s timeout and per-request memoisation. No numeric target exists (OPEN). Not measured.
- Security: SVG rejected, magic-byte typing, `nosniff`, relay allow-list, http/https links only. No dedicated penetration test.
- Auditability: Django admin history for edits (`LogEntry` test). Idle or other security events: out of scope.

## 6. Outcome
Overall status: **Ready for owner sign-off with limitations.**

Limitations and follow-ups:
- **Not executed / Partial:** visual, responsive, keyboard and dark-mode review of `/about` and the shell; real logo/favicon upload through the admin page in a browser; signed-in unavailable state on `/about`; profile-menu "About" entry in a browser. The owner should run these (steps: sign in, open About; upload images in `/admin/about/appidentity/`; stop Django and reload).
- Deviations the owner approved with the plan: `GET /api/v1/about/` is unpaginated but capped (D-1); the public identity endpoints (D-2).
- Small implementation choices to note: brand image has an empty `alt` because the app name is always adjacent (plan said "alt = app name"); the 50 / 30 / 30 caps are enforced by model and admin validation; `ui-preview/login` keeps the default brand.
- `manage.py migrate about` was run on the local dev database (it applied the schema and seed). The temporary test logo and favicon set during the smoke test were removed.
- Seed values for app name, description and copyright are the plan's proposals (OQ-P1); version is empty until the owner sets it in admin.
- No commit was made.

## 7. Change Log
| Date | Change | Reason | Approved by |
|---|---|---|---|
| — | — | — | — |

---
**Status:** Approved · **Approved by:** Project owner (`VALIDATION APPROVED`; owner confirmed the visual result, so the visual review is owner-accepted rather than executed by the agent) · **Date:** 2026-10-13
