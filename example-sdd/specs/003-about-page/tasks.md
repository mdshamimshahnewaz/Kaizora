# Task Breakdown — About Page

> **Purpose:** small, ordered, verifiable tasks that implement the approved `plan.md` (approved 2026-10-13) for the approved `spec.md`.
> **Location:** `specs/003-about-page/tasks.md`.
> **Approval does not authorise implementation.** Implementation starts only after the owner approves this list **and** gives a separate explicit instruction to implement (`docs/decisions.md` D-6).

## Conventions
- `[ ]` pending, `[x]` done, `[~]` in progress, `[!]` blocked. Order = execution order. Each task cites the plan section and spec items.
- Backend commands from `backend\`: `.\.venv\Scripts\python.exe manage.py check | makemigrations --check | test about | test accounts | test core`. Frontend from `frontend\`: `npm run lint | typecheck | test | build`.
- No `.env` file is read or edited by the agent. Owner-only steps are marked **[Owner]**.
- Before any Next.js code (T10 onward), read the guides named in plan §7 under `frontend/node_modules/next/dist/docs/`.
- Existing 001/002 tests must keep passing; run them after T9, T13 and T17.
- The plan's open points (OQ-P1 to OQ-P6) are taken as approved with the plan's proposed values. If the owner gives different values, only the seed (T3), limits (T5) or labels change.

## Backend
- [x] **T1 — Create the `about` app skeleton** _(depends on: none)_
  - Implements: Plan §2
  - Done when: `backend/about/` exists (apps, models, admin, services, api, urls, tests packages), `about` is in `INSTALLED_APPS`, `path('api/v1/about/', include('about.urls'))` is in `config/urls.py`, and `manage.py check` passes. No imports from `accounts` or `core` except the shared exception handler through DRF settings.
- [x] **T2 — Models and schema migration** _(depends on: T1)_
  - Implements: Plan §3, Spec US-1–5, US-7
  - Done when: `AppIdentity`, `CreditGroup`, `CreditMember`, `Acknowledgement` exist with the specified fields, lengths, ordering and URL validator; one migration applies cleanly on PostgreSQL; `makemigrations --check` is clean.
- [x] **T3 — Seed data migration** _(depends on: T2)_
  - Implements: Plan §3 (seed), Spec AC-5.3, AC-X.3
  - Done when: a data migration creates the identity (name "Timely", version empty, description "Workforce management", copyright "© 2025 - 2026 SEBPO BD"), the seven credit groups with their people, the OpenStreetMap acknowledgement and the special-thanks text exactly as listed in plan §3. It only seeds when tables are empty, is idempotent and its reverse does nothing. No other names are added.
- [x] **T4 — Service layer** _(depends on: T2)_
  - Implements: Plan §2, §4 (internal interface), Spec AC-2.1, 2.3, 3.2, 4.1, X.3
  - Done when: `get_identity()`, `get_about()` and `get_image(kind)` exist. Singleton get-or-create works on an empty DB. Groups and members are ordered by `sort_order` then id. Groups without members are omitted. Stored URLs not starting with http/https are omitted from output. `logo_version` and `favicon_version` are computed from the bytes.
- [x] **T5 — Image validation helper** _(depends on: T2)_
  - Implements: Plan §5, Spec AC-5.4 (logo/favicon), Edge cases
  - Done when: a pure function decides the type from magic bytes (logo PNG/JPEG/WebP ≤ 512 KB; favicon PNG/ICO ≤ 128 KB), rejects SVG, empty, oversize and mismatched content, and returns only an allow-listed content type. Unit tests cover each case.
- [x] **T6 — Django admin** _(depends on: T2, T4, T5)_
  - Implements: Plan §3, §5, Spec US-5, AC-5.1, 5.2, 5.4
  - Done when: `AppIdentity` admin allows one row only (no add when it exists, no delete) with upload fields and "remove" checkboxes for logo and favicon, using T5 validation and storing the type and version; `CreditGroup` admin has a `CreditMember` inline; `Acknowledgement` admin exists; `sort_order` is editable in lists; the admin rejects more than 50 groups, 30 members per group and 30 acknowledgements; access follows standard model permissions only.

## API contract
- [x] **T7 — Protected About endpoint** _(depends on: T4)_
  - Implements: Plan §4 `GET /api/v1/about/`, Spec AC-1.1, 2.1, 3.1, 4.1, X.1
  - Done when: returns the specified JSON with `Cache-Control: no-store`; 401 without a session; 200 for any authenticated user including one with no roles; response has no extra fields.
- [x] **T8 — Public identity and image endpoints** _(depends on: T4, T5)_
  - Implements: Plan §4 `identity/`, `identity/logo/`, `identity/favicon/`, §5, Spec AC-7.1, 7.4
  - Done when: `identity/` returns only `name`, `has_logo`, `logo_version`, `has_favicon`, `favicon_version`; image endpoints return bytes with an allow-listed `Content-Type`, `nosniff`, `inline`, and `Cache-Control: public, max-age=0, must-revalidate`; 404 when unset; the `v` query parameter is ignored; each public view has a docstring stating why it is public.

## Frontend
- [x] **T9 — Shared client additions and `lib/api/about.ts`** _(depends on: T7, T8)_
  - Implements: Plan §7, `docs/frontend-api-client.md` §3–4
  - Done when: `apiRequestBytes` exists in `lib/api/client.ts` (5 s timeout, `redirect: "error"`, no-store, 1 MB cap); `getAbout(session)` and `getIdentity()` exist with hand-written type guards; both are `server-only`; no direct Django `fetch` elsewhere.
- [x] **T10 — Brand source, fallback and provider** _(depends on: T9)_
  - Implements: Plan §2, §7, Spec AC-7.1, 7.3
  - Done when: `lib/brand.ts` defaults are unchanged; `getBrand()` (React `cache`) merges backend identity over defaults and falls back to defaults on any `ApiClientError` or invalid response, logging only the error kind and `request_id`; logo and favicon URLs are `/brand/logo?v=…` and `/brand/favicon?v=…` only when the backend says they exist; `BrandProvider` and a `useBrand()` hook exist.
- [x] **T11 — Image relay Route Handlers and `proxy.ts` exemption** _(depends on: T9)_
  - Implements: Plan §7 (BFF), Spec AC-7.4
  - Done when: `GET /brand/logo` and `GET /brand/favicon` fetch bytes through the shared client, forward only an allow-listed `Content-Type` plus `nosniff` and `Cache-Control: public, max-age=31536000, immutable`, and return 404 when Django answers 404 and a generic 502 on other failures; `proxy.ts` matcher and `decideGate` exempt `brand/`; the gate test is updated.
- [x] **T12 — Apply brand app-wide** _(depends on: T10, T11)_
  - Implements: Plan §7, Spec US-7, AC-7.1, 7.2, 7.3
  - Done when: `SessionShell` fetches user and brand in parallel and feeds `BrandProvider`; sidebar rail, header, drawer, footer, `BrandMark` (img when a logo exists, otherwise the current SVG mark; alt = app name), the sign-in page and `ui-preview/login` use the provided brand; `app/layout.tsx` uses `generateMetadata` for the title template (`%s | <name>`), description and favicon (default `app/favicon.ico` when none). With the backend stopped, the UI looks exactly as it does today.
- [x] **T13 — Navigation entries** _(depends on: T12)_
  - Implements: Plan §2, Spec US-6, AC-6.1
  - Done when: an `about` item (`/about`, an existing icon or one added to the icon map) is in the `main` group of `lib/navigation.ts` and passes `validateNavigation`; `profile-menu.tsx` has an enabled "About" entry linking to `/about`; existing disabled entries are unchanged.
- [x] **T14 — About page and components** _(depends on: T9, T12)_
  - Implements: Plan §7, Spec US-1–4, AC-1.2, 2.1–2.3, 3.2, 4.1, X.2–X.4
  - Done when: `app/about/page.tsx` calls `requireUser()` and `getAbout()`; `components/about/*` render the hero (logo or placeholder, name, version, description, copyright), credit-group cards, acknowledgements with safe external links (`target="_blank"`, `rel="noopener noreferrer"`), and the thanks note only when present; unavailable state with retry for network/timeout/5xx, empty state when there is no content; only design tokens (no raw colours); semantic headings; keyboard-friendly; responsive; page title set.

## Docs
- [x] **T15 — Update `docs/tech-stack.md`** _(depends on: T1, T11)_
  - Implements: Plan §2
  - Done when: the layout line lists `backend/about/` and the test command `manage.py test about`. (The BFF register entries were added on plan approval.)

## Tests and validation
- [x] **T16 — Backend tests** _(depends on: T3–T8)_
  - Implements: Plan §10, all backend ACs
  - Done when: `manage.py test about` passes and covers: service ordering, empty-group omission, bad-URL omission, version hash; API 401/200 and payload shape; public endpoints minimal payload, image headers and 404; a guard test that only the three identity views are public; admin permission, singleton, upload and cap validation, edit-then-fetch, `LogEntry`; seed content and idempotency. `manage.py test accounts` and `core` still pass.
- [x] **T17 — Frontend tests and static checks** _(depends on: T9–T14)_
  - Implements: Plan §10, all frontend ACs
  - Done when: tests added for the type guards, `getBrand` fallback and merge, the relay allow-list pure function, navigation (About item valid and active), the gate exemption and the profile-menu entry; `npm test`, `npm run lint`, `npm run typecheck` and `npm run build` pass; existing raw-colour, token, navigation and auth tests still pass.
- [~] **T18 — Manual verification (executed separately)** _(depends on: T16, T17)_
  - Implements: Plan §10 manual list
  - Done when: each item is Passed, Partial or Not executed with a note: light/dark and narrow/wide layout; keyboard pass; real logo and favicon upload in admin and the tab icon; signed-out sign-in page branding; Django stopped (fallback brand, unavailable state); admin edit visible on next load. **[Owner]** performs the steps that need a browser session if the agent cannot.
- [x] **T19 — Validation pass** _(depends on: T16–T18)_
  - Produces: `specs/003-about-page/validation.md` (from `sdd-templates/validation-checklist-template.md`), marked `Ready for approval`
  - Done when: every AC is Passed with executed evidence or explicitly Deferred with a reason; planned and executed validation are reported separately; `specs/README.md` is updated.

## Notes
- Out of scope per spec §9: custom editing UI, photos or contact details, release notes, automatic versioning, multi-language content.
- No new dependencies or infrastructure are planned. If one becomes necessary, stop and ask.
- Do not add tasks outside the approved plan; raise them for approval.

## Change Log
Changes after approval require re-approval and pause implementation (see `docs/sdd-workflow.md` §5).

| Date | Change | Reason | Approved by |
|---|---|---|---|
| — | — | — | — |

---
**Status:** Approved · **Approved by:** Project owner (`TASKS APPROVED`) · **Date:** 2026-10-13 · **Implementation authorised by owner:** Yes (2026-10-13)
