# Technical Plan — About Page

> **Purpose:** HOW the approved `spec.md` will be implemented. Every decision traces to a spec item.
> **Location:** `specs/003-about-page/plan.md`. **Rules:** `docs/constitution.md` (v1.1), `docs/architecture.md`, `docs/api-conventions.md`, `docs/frontend-api-client.md`.
> Every decision is marked CONFIRMED, PROPOSED, OPEN or DEFERRED. **Nothing in this plan is CONFIRMED yet.**
> Written from the approved spec (2026-10-13, incl. US-7). Existing code was read only.

## 1. Linked Spec
Source: `specs/003-about-page/spec.md` · Covers: US-1 to US-7, AC-1.1 to AC-7.4, AC-X.1 to AC-X.4.

## 2. Architecture Overview
- **Backend:** one new Django app `backend/about/` (module `about`), flat like `accounts`. It owns all About data, an admin, a small service layer and three read endpoints. It imports nothing from `accounts` or `core` (AR-5); it only relies on the project-wide DRF default (authenticated) for protected reads. **[PROPOSED; module structure is OPEN D-22, same shape as `accounts`]**
- **Frontend (presentation only):**
  - `app/about/page.tsx`: server component, calls `getAbout(session)` and renders the page with existing UI Foundation components.
  - `lib/api/about.ts`: typed shared-client functions (`getAbout`, `getIdentity`).
  - `lib/brand.ts` stays as the **default/fallback** brand (AC-7.3). A server function `getBrand()` (wrapped in React `cache`) merges backend identity over the defaults. `SessionShell` fetches the user and the brand in parallel and passes the brand to the shell through a small `BrandProvider` context (same pattern as `AccessProvider`). `app/layout.tsx` uses `generateMetadata`, and `app/login/page.tsx` calls `getBrand()` directly (server component).
  - `BrandMark` renders the uploaded logo as an `<img>` when one is set, else the existing SVG mark.
  - Two Route Handlers relay the logo and favicon bytes (see §7, BFF).
- **Navigation (US-6):** one item `about` appended to the `main` group in `lib/navigation.ts`; one enabled "About" entry added to `profile-menu.tsx`. Both link to `/about`.
- **Flow:** browser → Next.js → Django. The browser never calls Django (D-56, D-20).

## 3. Data Model and Ownership
Owner module for every table: `about`. No foreign keys to other modules (D-31 not needed).

```
Entity: AppIdentity (singleton, one row)     Owner: about
  name: varchar(60) — required — app name (AC-7.1)
  description: text(≤500) — blank ok — short description (AC-1.1)
  version: varchar(32) — blank ok — entered by hand (AC-5.4)
  copyright_text: varchar(200) — blank ok
  special_thanks: text(≤1000) — blank ok (AC-4.1)
  logo_data: binary — null ok;  logo_content_type: varchar(32);  logo_version: varchar(12)
  favicon_data: binary — null ok; favicon_content_type: varchar(32); favicon_version: varchar(12)
  updated_at: datetime
  (logo_version / favicon_version = first 12 hex chars of SHA-256 of the bytes; used for cache busting)

Entity: CreditGroup        Owner: about
  title: varchar(100) — required;  sort_order: int — default 0

Entity: CreditMember       Owner: about
  group: FK CreditGroup (CASCADE);  name: varchar(120) — required
  designation: varchar(160) — blank ok (e.g. "Project Manager (Ex.")  — AC-2.2)
  sort_order: int — default 0

Entity: Acknowledgement    Owner: about
  name: varchar(100) — required;  used_for: varchar(200) — blank ok
  attribution_text: varchar(300) — blank ok
  url: URL — blank ok — http/https only (AC-3.2);  sort_order: int — default 0
```
- Singleton: the admin disallows a second row and deletion; the service layer uses get-or-create so an empty database never fails (AC-X.3).
- Images live **in PostgreSQL as bytes**, not on the filesystem. This avoids media-file configuration, backups of a second store, an image library (Pillow) and any production file-hosting decision (hosting is OPEN). Size caps keep rows small. **[PROPOSED]**
- Migrations: schema migration, then a data migration that seeds the old application's content (AC-5.3). Seed is idempotent (only when tables are empty) and its reverse does nothing.
  - Seeded credit groups and people (from the owner's reference, to be corrected later in admin): Planning & Coordination (Tanveer Mohammad Noman, CTO; Md. Shamim Shahnewaz, Project Manager); System Architecture & Backend (Md. Shamim Shahnewaz, Project Manager); Core Features & APIs (Md. Shamim Shahnewaz, Project Manager; Fehor Ahmed, Software Engineer; Main Uddin Sumon, IT (Ex. NSA)); User Interface & Experience (Md. Aliul Haque, Senior Creative Designer; Hasinul Alam Sujan, Project Manager (Ex.)); Testing & Bug Tracking (Abdul Awal Kiron, Senior QA Engineer); Data Management & Support (Sajjad Hossain Rabbi, Assistant Manager IT; Md. Towhiduzzaman, Deputy Manager IT); Infrastructure & Deployment (Sabbir Rahman Shuvo, Manager NSA).
  - Seeded acknowledgement: OpenStreetMap, attribution "Map data © OpenStreetMap contributors", link to `https://www.openstreetmap.org/copyright`.
  - Seeded special thanks: "All team members & colleagues who provided guidance, support and encouragement."
  - Seeded identity: **see OQ-P1** (name, version, description, copyright are not fully known).
  - Spelling is copied from the screenshot as is. The owner fixes any errors in admin.

## 4. API Contract
Base `/api/v1/about/`. All JSON except the two image endpoints. Errors use the existing envelope (`accounts.api.exceptions`); the About views reuse that handler (no new handler) so the two modules stay decoupled only at the DRF settings level.

```
GET /api/v1/about/
  Purpose:        Full About content (US-1–4; AC-1.1, 2.1, 2.3, 3.1, 4.1)
  Auth:           authenticated (project default, session header)
  Permission:     any authenticated user (all roles) — spec §4
  Response 200:   {
                    "identity": {"name","description","version","copyright_text",
                                 "has_logo","logo_version","has_favicon","favicon_version"},
                    "credit_groups": [{"title","members":[{"name","designation"}]}],   // empty groups omitted, ordered
                    "acknowledgements": [{"name","used_for","attribution_text","url"}],
                    "special_thanks": "" 
                  }
  Pagination:     none — see deviation D-1 below
  Errors:         401 not signed in / expired session
  Headers:        Cache-Control: no-store

GET /api/v1/about/identity/
  Purpose:        App identity for app-wide branding, including before sign-in (US-7; AC-7.1, 7.4)
  Auth:           PUBLIC (explicit exception, justification in §5)
  Response 200:   {"name","has_logo","logo_version","has_favicon","favicon_version"}
  Errors:         none expected; empty database returns the seeded/default name
  Headers:        Cache-Control: no-store

GET /api/v1/about/identity/logo/     GET /api/v1/about/identity/favicon/
  Purpose:        Image bytes (US-7)
  Auth:           PUBLIC (same justification)
  Response 200:   image bytes; Content-Type from an allow-list; X-Content-Type-Options: nosniff;
                  Content-Disposition: inline; Cache-Control: public, max-age=0, must-revalidate
  Errors:         404 when no image is set
```
- The query string `v=<version>` that the frontend adds is ignored by Django; it only changes the URL the browser caches.
- Writing is **not** exposed through the API. Editing happens only in Django admin (spec §4).
- Internal interface (not HTTP): `about.services.get_about()`, `get_identity()` and `get_image(kind)`, used by the views. No other module calls them yet.

**Deviations from the PROPOSED conventions (owner decision needed, OQ-P3):**
- **D-1:** `GET /api/v1/about/` is not paginated (api-conventions §3). It is a single curated document, not a list collection. The plan caps it: the admin rejects more than 50 groups, 30 members per group and 30 acknowledgements, so it stays bounded.
- **D-2:** `identity` and the image endpoints are public (api-conventions §6 allows this only as an explicit, justified exception).

## 5. Security
- **AuthZ:** deny by default. `GET /about/` uses the DRF default (`IsAuthenticated`). Only the three identity endpoints set `AllowAny` and `authentication_classes([])`, each with a docstring stating why (as `login_start` does). A test fails if any other About view becomes public.
- **Why public is acceptable (AC-7.4):** the sign-in page and the favicon must render before sign-in. The public payload is the app name and two image files only, with no personal data, version or content. **[PROPOSED, needs owner confirmation, OQ-P2]**
- **Input / upload validation (admin only):**
  - Logo: PNG, JPEG or WebP, ≤ 512 KB. Favicon: PNG or ICO, ≤ 128 KB. **[PROPOSED limits, OQ-P4]**
  - Type is decided from the file's magic bytes, not the file name or the browser-supplied type. SVG is rejected (script risk). The stored `content_type` comes from this check only.
  - `url` must be `http` or `https` (model validator, run in admin and checked again when serialising: a bad stored value is omitted from output).
  - Field lengths enforced by model constraints.
- **Output:** JSON is escaped by React on render. No `dangerouslySetInnerHTML` for About text. External links render with `target="_blank"` and `rel="noopener noreferrer"` (AC-3.2).
- **Images:** served with `nosniff` and a fixed allow-listed `Content-Type`; the Next.js relay re-checks that type and forwards nothing else.
- **Admin access:** Django admin with the standard model permissions (`add/change/delete/view` on each About model). The default Django admin login and `is_staff` are used; no new role system is created. Non-staff users cannot reach it (AC-5.2). *How admin accounts are created is existing behaviour (superuser tools) and is outside this feature; flagged as OQ-P5.*
- **Secrets / logs:** none involved. Request errors log `request_id` only.
- **Audit:** admin edits are recorded by Django's built-in admin history (`LogEntry`), as the spec states. No custom audit events (P5 audit events remain OPEN, D-30).

## 6. External Systems and Adapters
None. OpenStreetMap and others are text and links only.

## 7. Frontend
- **Pages/components:** `app/about/page.tsx` plus small presentational components under `components/about/` (identity header, credit-group cards, acknowledgements list, special-thanks block) built from existing UI Foundation parts and tokens only. No raw colours (`raw-colors` test). Modern layout: hero with logo, name, version and description; responsive grid of role cards; acknowledgement list with an external-link icon; keyboard-friendly, semantic headings (AC-X.4).
- **Shared client:** `lib/api/about.ts` with type guards (no schema library, per `docs/frontend-api-client.md` §4). `lib/api/client.ts` gets one small addition, `apiRequestBytes`, for the image relay (same 5 s timeout, `redirect: "error"`, no-store, size limit of 1 MB).
- **Brand data path:** `getBrand()` = `cache(async () => merge(defaults, await getIdentity()))`. On any `ApiClientError` it returns the defaults (AC-7.3) and logs only the error kind and `request_id`. Logo URL is built as `/brand/logo?v=<logo_version>` only when `has_logo`; favicon likewise.
- **App-wide surfaces (AC-7.2, PROPOSED):** the sidebar-rail home link, header brand name and mark, drawer title and brand, footer text, sign-in page, browser-tab title and favicon, `ui-preview/login`. Tab title format: `<page title> | <app name>` as today (OQ-P6). The current `brand.tagline` stays a fixed default (not managed in admin).
- **Pre-sign-in:** `proxy.ts` matcher gets `brand/` added to its exclusion list so the two Route Handlers are reachable without a session cookie. `lib/auth/gate` and its test are updated accordingly.
- **Error / empty states:** `/about` uses the existing error-map and states components: 401 → sign-in (existing `requireUser` flow), network/timeout/5xx → unavailable state with retry, nothing hard-coded as content (AC-X.2). Empty tables → empty state (AC-X.3).
- **Images:** a plain `<img>` is used (same-origin relay, no optimiser config, no new `next.config` change). The lint exception is local and commented. Alt text is the app name.
- **Next.js docs to read before coding (AGENTS.md):** `01-app/01-getting-started/14-metadata-and-og-images.md`, `15-route-handlers.md`, `06-fetching-data.md`, `03-api-reference/04-functions/fetch.md` under `frontend/node_modules/next/dist/docs/`. Implementation must follow what they say about `generateMetadata` with request-time data under the existing Suspense layout.
- **BFF / Route Handlers (register entry needed in `docs/architecture.md` §3, owner approval):**

| Handler | Justification | Must not |
|---|---|---|
| `GET /brand/logo` | Relays binary image bytes from Django. The browser may not call Django (D-56), so an image `src` needs a same-origin URL. | No business rules, no auth decisions, no caching beyond headers, no other content types. |
| `GET /brand/favicon` | Same, for the favicon `<link>`. | Same. |

## 8. Tech Choices & Trade-offs
| Decision | Options considered | Chosen | Status | Why |
|---|---|---|---|---|
| Where to keep images | Filesystem media; DB bytes; static files | DB bytes (`BinaryField`) | PROPOSED | No media config or hosting decision, no Pillow, one backup. Cost: small size caps. |
| How the browser gets images | Browser calls Django; base64 in JSON; Route Handler relay | Route Handler relay, `?v=` cache busting | PROPOSED | Keeps D-56 intact, keeps JSON small, allows long browser caching. |
| Image validation | Pillow; magic-byte check | Magic-byte check in own code | PROPOSED | No new dependency (P7). |
| Singleton pattern | `django-solo`; own get-or-create | Own get-or-create + admin guard | PROPOSED | No new dependency. |
| Ordering | Drag-drop admin; integer `sort_order` | Integer `sort_order` | PROPOSED | Simplest, works in stock admin. |
| Seed | Fixture; data migration | Data migration | PROPOSED | Runs with `migrate`, idempotent. |
| Brand data into client components | Fetch in each; context provider | `BrandProvider` fed from `SessionShell` | PROPOSED | One fetch per request, matches `AccessProvider`. |

**New dependencies or infrastructure: None.**

## 9. Traceability Matrix
| Spec item | Plan section | Notes |
|---|---|---|
| US-1 / AC-1.1, 1.2 | §3, §4 `GET /about/`, §7 | Placeholder mark when no logo |
| US-2 / AC-2.1–2.3 | §3, §4, §7 | Empty groups omitted server-side; "Ex." via designation text |
| US-3 / AC-3.1, 3.2 | §3, §5, §7 | URL validator, safe link attributes |
| US-4 / AC-4.1 | §3, §4 | Empty note → block hidden |
| US-5 / AC-5.1–5.4 | §3, §5 | Admin, seed migration, manual version |
| US-6 / AC-6.1 | §2, §7 | Sidebar `main` group + profile menu |
| US-7 / AC-7.1–7.4 | §4 `identity*`, §5, §7 | Public minimal payload; fallback brand |
| AC-X.1 | §4, §5 | Default auth; `proxy.ts` + page `requireUser` |
| AC-X.2, X.3 | §7 | Unavailable and empty states |
| AC-X.4 | §7 | Tokens, semantic markup, keyboard |

## 10. Testing Strategy
- **Backend (Django test runner, `manage.py test about`):**
  - Service: get-or-create singleton; empty groups omitted; ordering; bad stored URL omitted; version hash changes with the bytes.
  - API: unauthenticated `GET /about/` → 401 (AC-X.1); authenticated user with no roles → 200 (all roles); identity and image endpoints public with the minimal payload only; image 404 when unset; correct `Content-Type`, `nosniff`; no field leakage; "every other view is protected" guard test.
  - Admin: only staff with permission can add/change; singleton cannot be added twice or deleted; upload validation (wrong magic bytes, SVG, oversize, mismatched extension, bad URL scheme) rejected; edit then fetch shows the change (AC-5.1); `LogEntry` written.
  - Migration: seed creates the expected groups and people, is idempotent, and does not touch existing rows.
- **Frontend (`npm test`, Node test runner as today):** `getAbout`/`getIdentity` type guards and error mapping; `getBrand` fallback on error and on empty identity; navigation test (About item valid, active path); gate test for `brand/` exclusion; profile-menu entry; raw-colours and token tests still pass; image relay allow-list logic (extracted as a pure function). Existing 001/002 tests must keep passing.
- **Static checks:** `npm run lint`, `npm run typecheck`, `npm run build`, `manage.py check`, `manage.py makemigrations --check`.
- **Manual (reported separately, not counted as Passed until run):** visual review in light/dark and at narrow/wide widths; keyboard pass; real logo/favicon upload in admin and the tab icon; sign-in page branding while signed out; Django stopped → fallback brand and unavailable state.
- Existing tests are not changed except where the brand source or `proxy` matcher demands it.

## 11. Risks & Mitigations
- Identity fetched on every page render adds a call and a failure point → 5 s timeout, `cache()` dedupe per request, graceful fallback, no stale content; if too slow, a short server-side cache is a later, separately approved change.
- `generateMetadata` with request-time data under the existing layout may behave differently in this Next.js version → read the docs first (§7), verify with `npm run build` and a manual tab-title check.
- Changing the shared brand source touches 001 and 002 UI → keep `lib/brand.ts` defaults identical to today's, so a missing backend looks exactly like now; run all existing tests.
- Binary rows in PostgreSQL → caps (512 KB / 128 KB) and a single-row table.
- Seeded names may be wrong or outdated → clearly stated in the spec; editable in admin.
- Public endpoints expose the app name and logo → accepted by design, limited to those fields, and a test locks the payload shape.
- Admin accessibility depends on how staff accounts exist → OQ-P5.

## 12. Constitution Check
| Principle | Compliant? | Notes |
|---|---|---|
| P1 Spec first, gates | Yes | Approved spec; this plan awaits approval. Existing 001/002 behaviour changes only as US-7 requires. |
| P2 Decisions labelled | Yes | Everything is PROPOSED; open points in §13 (OQ-P1–P6). |
| P3 Modular monolith | Yes | New `about` module, no cross-module imports; module structure is OPEN (D-22) and flagged. |
| P4 Adapters for external systems | Yes | No external systems. |
| P5 Security, privacy, audit | Yes, with flags | Server-side auth; public endpoints minimal and justified; admin history for audit; audit events OPEN (D-30). |
| P6 Evidence-based validation | Yes | Automated tests per AC; manual checks reported separately. |
| P7 Minimal footprint | Yes | No new dependency or infrastructure; no Docker/WSL; no AI. |
| P8 API-first | Yes | DRF holds data and rules; Next.js presents; two justified relay handlers; no DB access from the frontend. |

## 13. Open Points for the Owner
- **OQ-P1 Seed values:** initial **app name** (current code uses "Timely"; the old page said "TimeLy"), **version** (old page said 3.0.0; V4 value unknown), **description** and **copyright** (old footer: "© 2025 - 2026 SEBPO BD"). Proposed seed: name "Timely", version empty until you set it, description "Workforce management", copyright "© 2025 - 2026 SEBPO BD". Confirm or give values.
- **OQ-P2:** Confirm public minimal identity (AC-7.4, D-2).
- **OQ-P3:** Approve deviation D-1 (not paginated, capped).
- **OQ-P4:** Confirm upload limits and types (logo PNG/JPEG/WebP ≤ 512 KB; favicon PNG/ICO ≤ 128 KB; no SVG).
- **OQ-P5:** Who gets Django admin access (staff/superuser accounts, existing process)? No new role system is planned.
- **OQ-P6:** Confirm the AC-7.2 surface list and tab-title format `<page> | <app name>`.
- Spec items still PROPOSED: AC-7.2, AC-7.4, OQ-4 (they stay so until the owner confirms them above).
- **BFF register** entries for `GET /brand/logo` and `GET /brand/favicon` need approval with this plan (`docs/architecture.md` §3 is updated only after approval).

## 14. Change Log
| Date | Change | Reason | Approved by |
|---|---|---|---|
| — | — | — | — |

---
**Status:** Approved · **Approved by:** Project owner (`PLAN APPROVED`, as written, including the proposals and open points in §13) · **Date:** 2026-10-13
