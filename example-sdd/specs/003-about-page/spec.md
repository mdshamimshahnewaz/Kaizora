# Feature Spec — About Page

> **Purpose:** WHAT is being built and WHY, with no technical solution. Technical decisions are in `plan.md`.
> **Location:** `specs/003-about-page/spec.md`. **Rules:** `docs/constitution.md` (P2, P3, P5, P8), `docs/architecture.md`.
> **Process note:** drafted in the conversation on 2026-10-13. The owner approved it with fixes (their answers to the draft's open questions), which are incorporated below.

## 1. Summary
An independent "About" module that shows the application's identity (name, logo, favicon, version, description, copyright), credits (who worked in which role or area), acknowledgements of third-party services/APIs/open data used, and a special-thanks note. All content comes from the backend and is maintained by administrators through Django admin; the frontend holds no hard-coded About content. The design is new, built on the UI Foundation (001) in a modern style. The old application's About page is a content reference only, not a design reference. **[CONFIRMED]**

## 2. User Stories
- **US-1 (P0):** As a signed-in user, I want to see the application name, logo, version, short description and copyright, so that I know what I am using.
- **US-2 (P0):** As a signed-in user, I want to see credits grouped by role/area (for example Planning & Coordination, System Architecture & Backend, Core Features & APIs, User Interface & Experience, Testing & Bug Tracking, Data Management & Support, Infrastructure & Deployment) with each person's name and designation, so that contributors are acknowledged.
- **US-3 (P0):** As a signed-in user, I want to see which external services, APIs or open data the application uses (for example OpenStreetMap) with attribution text and a link, so that attribution obligations are met.
- **US-4 (P1):** As a signed-in user, I want to see a special-thanks note, so that the wider team is acknowledged.
- **US-5 (P0):** As an administrator, I want to manage all About content (app name, logo, favicon, version, description, copyright, credit groups and people, acknowledgements, thanks note) in Django admin, so that no code change is needed.
- **US-6 (P0):** As a signed-in user, I want to open About from the sidebar main menu and from the profile menu, so that it is easy to find.
- **US-7 (P0):** As an administrator, I want the application name, logo and favicon I set in Django admin to be used everywhere the app shows its identity, so that I change branding in one place.

## 3. Acceptance Criteria
### US-1
- **AC-1.1:** Given a signed-in user, when they open About, then app name, logo, version, description and copyright are shown from backend data.
- **AC-1.2:** Given no logo is set, then a neutral placeholder is shown and nothing breaks.

### US-2
- **AC-2.1:** Given credit groups exist, when the page loads, then groups appear in the admin-defined order, each with title and its people (name + designation) in the admin-defined order.
- **AC-2.2:** A former member can be marked as former (shown like "Ex.") by editing the designation text; no separate mechanism is required.
- **AC-2.3:** A group with no people is not shown.

### US-3
- **AC-3.1:** Each acknowledgement shows service name, what it is used for, attribution text and an optional link.
- **AC-3.2:** External links open safely (new tab, no opener/referrer leak). Only http/https links are accepted and rendered.

### US-4
- **AC-4.1:** The special-thanks note is shown when present and hidden when empty.

### US-5
- **AC-5.1:** Given an administrator in Django admin, when they edit any About content, then the change appears in the page on the next load.
- **AC-5.2:** Given a non-administrator, then they cannot edit About content (read-only for everyone else).
- **AC-5.3:** The initial data contains the names, designations and role groups from the old application's About page (owner will correct them later in admin). No other names are invented.
- **AC-5.4:** App name, logo and favicon are managed as part of About content. Version is a manually entered value that the owner keeps in line with the git version/release by hand.

### US-6
- **AC-6.1:** Given a signed-in user, then an "About" item exists in the sidebar main menu and in the profile menu, and both open the same page.

### US-7
- **AC-7.1:** Given an administrator changes the app name, logo or favicon in Django admin, when any page loads next, then every place that shows app identity uses the new value, with no code change.
- **AC-7.2 (PROPOSED surfaces, owner to confirm):** sidebar brand, browser-tab title and favicon, sign-in page, About page, and any other place the app name/logo is displayed.
- **AC-7.3:** Given the identity data cannot be loaded (backend down, nothing set, or not yet signed in on the sign-in page), then the UI shows a neutral placeholder/default and stays usable. Where the default comes from is decided in `plan.md`.
- **AC-7.4:** Identity data needed before sign-in (sign-in page, favicon, tab title) is exposed without login and contains only app name, logo and favicon. Everything else in About stays login-required (AC-X.1). **[PROPOSED]**

### Cross-cutting
- **AC-X.1:** Given an unauthenticated visitor, when they request About data or the page, then access is refused and they are sent to sign-in (login required, per 002).
- **AC-X.2:** Given the backend is unavailable or returns an error, then the page shows a clear error state with retry and no fallback hard-coded content.
- **AC-X.3:** Given an empty database, then the page shows a sensible empty state instead of failing.
- **AC-X.4:** The page is responsive, keyboard-accessible and follows UI Foundation theming. Content is English only.

## 4. Operations Clients Need
| Operation | Who may perform it | Related AC |
|---|---|---|
| Read all About content (app info, credits, acknowledgements, thanks note) | Any signed-in user (all roles) **[CONFIRMED]** | AC-1.1–4.1, AC-X.1 |
| Create / edit / reorder / remove About content | Administrators via Django admin only **[CONFIRMED]** | AC-5.1–5.4 |
| Read app identity (name, logo, favicon) for app-wide use, including before sign-in | Anyone **[PROPOSED]**, see AC-7.4 | AC-7.1–7.4 |

## 5. Data and Ownership (business level)
- Owned only by the About module; other modules do not read or write its data, and it does not read theirs (P3).
- Data: application identity (name, logo, favicon, version, description, copyright), credit groups, people (name, designation), acknowledgements, special-thanks note.
- Sensitivity: staff names and designations (low–moderate personal data). No contact details, photos or profile links. No secrets.
- Freshness: admin changes visible on next load. Retention: **DEFERRED**.

## 6. External Systems and Dependencies
- External systems: none are called. Acknowledged services are only text and links.
- Depends on 001 (UI Foundation: App Shell, sidebar, profile menu, theming) and 002 (authentication: login required).
- **Changes existing behaviour:** US-7 replaces the currently fixed app name/logo/favicon in the 001 App Shell and the 002 sign-in page with About-managed values. This is an approved requirement change under P1/P7 and must keep those features' existing tests passing (plan states how).

## 7. Non-Functional Requirements
- Performance: one lightweight read per page view. Numeric targets **OPEN** (D-29/D-30).
- Security: server-side authorisation; all text is escaped on render; uploaded logo/favicon limited to safe image types and size (limits set in plan).
- Auditability: admin edits of About content are recorded by the standard Django admin history. Specific audit events remain **OPEN** (P5).
- Accessibility/i18n: semantic headings, sufficient contrast, keyboard use. English only **[CONFIRMED]**.

## 8. Edge Cases & Error States
Empty data; very long names or text; missing link or logo; unsafe link scheme rejected; invalid or oversized image upload rejected; backend unavailable; two admins editing at once; expired session (handled by 002).

## 9. Out of Scope
- Copying the old page's visual design or emoji icons.
- Photos, contact details or profile links for people.
- Changelog/release notes, licence-text viewer, analytics.
- A custom (non-Django-admin) editing UI.
- Linking credit roles to application permission roles (credit roles are free-text group titles) **[CONFIRMED]**.
- Automatic version derivation from git.
- Multi-language content.
- AI features.

## 10. Open Questions
Resolved by the owner on 2026-10-13: access = login required; maintenance = Django admin; initial data = old names; version = manual; language = English; entry points = sidebar main menu + profile menu; visibility = all roles.

- **OQ-1 (resolved 2026-10-13):** App name, logo and favicon are used app-wide (US-7). The owner's words: "app relate content data like name logo icon ami sob jagay use korte chai".
- **OQ-2 (DEFERRED):** Data retention for About content.

Remaining for owner:
- **OQ-3:** Confirm the surfaces in AC-7.2 and the pre-login exposure of name/logo/favicon in AC-7.4 (needed for the sign-in page and favicon).
- **OQ-4:** Should the browser-tab title and other labels use only the app name, or name plus page title (for example "About · TimeLy")? Proposed: page title + app name.

## 11. Change Log
| Date | Change | Reason | Approved by |
|---|---|---|---|
| 2026-10-13 | Added US-7 and AC-7.1–7.4 (app name/logo/favicon used app-wide); resolved OQ-1; added OQ-3, OQ-4 | Owner asked to use app identity data everywhere | Project owner, 2026-10-13 |
| 2026-10-13 | App-wide brand also uses the About description as the header and footer tagline (signed-in pages only; the public identity payload is unchanged) | Owner request in conversation after implementation | Owner request (conversation); formal re-approval pending |

---
**Status:** Approved · **Approved by:** Project owner (`SPEC APPROVED`, including US-7) · **Date:** 2026-10-13 · **Linked constitution:** `docs/constitution.md` (v1.1)
