# Feature Spec — UI Foundation (v2)

> **Purpose:** WHAT is being built and WHY, with no technical solution. Implementation details belong in `plan.md`.
> **Location:** `specs/001-ui-foundation/spec.md`. **Rules:** `docs/constitution.md`, `docs/architecture.md`.
> **Version:** v2 (revision of the approved v1 after the owner's `CHANGES REQUESTED`, 2026-10-11). **Status: Approved (2026-10-11).** **Owner decisions Q1 to Q7 were recorded on 2026-10-11** (see §10) and are reflected below.
> **Status labels:** CONFIRMED, PROPOSED, OPEN, DEFERRED. Nothing in v2 is CONFIRMED until the owner approves it, except items the owner stated in the change request, which are marked *(owner-directed)* and become CONFIRMED on approval of v2.
> Reference evidence and limits: `specs/001-ui-foundation/reference-analysis.md` (v2).

## 1. Summary
A shared UI foundation for Timely V4: design tokens, light and dark themes, an application shell, page layout rules, reusable components, responsive behavior, accessibility and standard UI states. **The OkyAi dashboard (https://okyai.mantrakshdevs.com/dashboard) is the primary visual and UX reference, and the target is a close visual match** in layout, shell, sidebar, header, spacing, density, type hierarchy, cards, controls, responsive behavior and theme presentation, while keeping Timely's own name, brand, icons and assets and meeting WCAG 2.2 AA. It has no business logic, no new backend endpoints and no feature pages.

**What changed from v1:** SmartHR is replaced by OkyAi. The design target moves from "followed conceptually" to "close visual match". The shell, tokens, shape, spacing, type, components and responsive behavior are redefined from measured reference values. Scope boundaries, non-functional requirements, the stack and the existing health-status behavior are unchanged.

## 2. User Stories
- **US-1 (P0):** As a developer, I want shared tokens and components, so that new pages are consistent without style decisions.
- **US-2 (P0):** As a user, I want one consistent shell and page layout, so that I navigate every module the same way.
- **US-3 (P0):** As a user, I want clear loading, empty, error, success and denied states.
- **US-4 (P0):** As a user, I want light and dark themes.
- **US-5 (P0):** As a user on any device, or using a keyboard or assistive technology, I want the app to meet WCAG 2.2 AA.
- **US-6 (P0):** As the product owner, I want brand colors, logo and typography to be changeable in one place, so that the official brand can be applied later without touching feature code.
- **US-7 (P1):** As the product owner, I want ownership and exception rules for shared components, so that the design doesn't drift.
- **US-8 (P0, new):** As the product owner, I want the application to look and behave like the OkyAi reference (shell, sidebar, header, cards, controls, spacing and type), so that Timely V4 has the intended visual identity from the first feature.

## 3. Acceptance Criteria
Unchanged from v1 unless marked **(revised)** or **(new)**.

- **AC-1.1:** Given any feature page, when reviewed, then all colors, spacing, type sizes, radii and shadows come from shared tokens, with no arbitrary values.
- **AC-1.2:** Given a UI element in the inventory, when a feature needs it, then the shared component is used.
- **AC-2.1 (revised):** Given any authenticated page, then it renders inside the shell with the reference's page structure: an optional quiet breadcrumb line, an H1 title, an optional muted description and a right-aligned actions area.
- **AC-2.2 (revised):** Given the sidebar, then at 1280 px and wider it is a fixed icon rail whose items have accessible names (tooltips and programmatic names), and below 1280 px it is an off-canvas drawer with labels opened from a header toggle. The current route is marked visually and with `aria-current="page"`. Nested groups expand and collapse.
- **AC-2.3:** Given a destination the user may not use, then it is not listed. The server still enforces access (P5).
- **AC-3.1:** Given any data region, then it defines loading, empty and error states. Errors offer retry where possible, show `request_id` when available, and never expose secrets or stack traces.
- **AC-3.2:** Given 401, 403, 404, network failure or 5xx, then the UI follows `docs/frontend-api-client.md` §4.
- **AC-3.3:** Given a successful user action, then a non-blocking success message appears and is announced to assistive technology.
- **AC-4.1 (revised):** Given light, dark or "follow system", then the UI uses semantic tokens only, with no flash of the wrong theme on load, and both themes present the reference's look (translucent surfaces, gradients, glow background) with contrast met in each.
- **AC-5.1 (revised):** Given widths of about 320, 390, 768, 1024, 1280 and 1440 px, then the shell and every inventory component are usable, with no horizontal page scroll.
- **AC-5.2 (keyboard):** Given keyboard-only use, then every interactive element is reachable in a logical order and operable. There are no keyboard traps, dialogs and drawers trap focus and restore it on close, and menus and tooltips follow standard keyboard behavior (Esc closes, arrows move in menus).
- **AC-5.3 (contrast, revised):** Given both themes, then text contrast is at least 4.5:1 (3:1 for large text), and UI component boundaries, icons and focus indicators at least 3:1, **measured against the composited background** (translucent surfaces over the glow background, and text on gradients). Verified by computing the token pairs. Where the reference falls short (reference-analysis §3), Timely deviates and records the deviation.
- **AC-5.4 (focus):** Given any focusable element, then the focus indicator is visible, meets 3:1 and is never obscured by sticky headers or sidebars (WCAG 2.2: 2.4.11).
- **AC-5.5 (targets):** Given pointer targets, then they are at least 24×24 CSS px, or spaced (WCAG 2.2: 2.5.8).
- **AC-5.6 (semantics):** Given the shell and components, then landmarks, heading order, form labels and errors (programmatically associated), live regions for notifications and `prefers-reduced-motion` are respected.
- **AC-5.7 (reflow):** Given 320 px width or 400% zoom, then content reflows without loss, except data tables that scroll within their own container.
- **AC-6.1:** Given a change to the provisional palette, logo or font, then it is made only in the centralized token and brand definitions, with no component or page edits required.
- **AC-7.1:** Given a proposed new shared component or design exception, then it has a recorded justification and owner approval before merge.
- **AC-8.1 (revised v3, owner-approved 2026-10-11, shell fidelity):** Given the shell at 1440 px, then the measured values match the approved v3 implementation within ?2 px: header height 72 px with a 24 px curve (`--curve`) at its four corners, rail width 88 px with the same 24 px curve, content offset 144 px (`--shell-left`) with fluid width up to a 48 px right margin, 40 px controls and 24 px cards. The rail panel is vertically centred and sizes to its items. At 1024 and 768 px the rail is replaced by the header toggle and drawer. The v2 values (96 px rail, 16 px corners, 1280 px container, 56?47 px rail items) are superseded.
- **AC-8.2 (new, surface and control fidelity):** Given cards and controls, then card radius is 24 px with 1 px border and about 27 px padding, control height is 40 px with 8 px radius, and the base spacing unit is 0.28 rem, within ±2 px of the observed values.
- **AC-8.3 (new, type hierarchy):** Given page and card headings and body text, then they follow the observed hierarchy (H1 30/36 bold, card title 18/28 semibold, body 14/20, small caps label, large metric value 30 bold) in Geist (Q2).
- **AC-8.4 (new, visual review):** Given the reference screens that map to the foundation (a dashboard-style page of metric cards, and a settings-style form page with icon-tile cards and toggle rows), when the same layouts are composed from shared components in the preview, then side-by-side screenshots at 1440, 1024, 768 and 390 px in both themes are produced and **the owner reviews them and records accept or changes**. The review includes a list of the typographic differences between Geist and the reference font and of every AA-driven deviation. Items the reference does not show (tables, dialogs, dropdowns, toasts, hover and focus) are not claimed to match.
- **AC-8.5 (new, scope and legal):** Given the shipped UI, then it contains no OkyAi logo, image, illustration, color set or copied source, no product-specific AI content, no search, notification or user placeholders, no customiser tab and no promotional card.

**Permission cases:** UI Foundation grants no permissions. AC-2.3 and AC-3.2 only reflect server decisions.

## 3A. Functional Requirements
*(Added section: the spec template has no place for functional or design requirements.)*

**CONFIRMED by approval of v2 (owner-directed in the change request)**
- **UI-FR-1 (revised)** OkyAi is the primary visual and UX reference and the target is a close visual match. No OkyAi source code, assets, logos, illustrations, branding or dependencies are copied, and no product-specific AI features are adopted.
- **UI-FR-5** Next.js, React, TypeScript and Tailwind v4 are kept. No Bootstrap, SCSS or new component framework. No dependency is added without explicit approval.
- **UI-FR-6 (revised)** The first scope is shell, tokens, themes, essential components, responsive behavior, accessibility and standard states, as in the reference's visual language.
- **UI-FR-10 (accessibility)** The target is WCAG 2.2 AA, measured through AC-5.x.
- Timely keeps its own product name, branding and icons. Light and dark themes are kept. No functional search, notifications or other business functionality is added because the reference contains them.
- The existing health-status functionality and the API-first architecture are preserved.

**Retained from v1 (CONFIRMED in v1)**
- **UI-FR-3** Semantic tokens: primary, secondary, surface (levels), text (default, muted, inverse), border, success, warning, danger, info and focus ring. They are centralized and per theme, and components never use raw palette colors.
- **UI-FR-4** Light and dark themes.
- **UI-FR-7 (icons)** Tabler Icons (owner-approved, installed).
- **UI-FR-8 (primitives)** Accessibility-sensitive interactions use established accessible primitives (Radix, owner-approved, installed).

**PROPOSED (new or revised in v2)**
- **UI-FR-2 (revised again 2026-10-11, owner correction after reviewing the implementation; supersedes decision Q1's blue-to-teal direction)** The provisional Timely palette follows the reference's overall character: a vivid violet → purple → magenta gradient for header and rail, a purple-tinted near-black dark background, a soft lavender-tinted light background, translucent purple-tinted dark surfaces and soft white light surfaces. No exact OkyAi color value, logo, text or asset is used, and Timely branding is kept. WCAG 2.2 AA takes priority over exact reproduction. The values are in plan §7.1 (v3 note) and `app/globals.css`. It is not brand approval. Earlier text follows for history: **UI-FR-2 (revised, owner decision Q1)** A **Timely-specific provisional palette** is used until official brand guidelines are supplied. It keeps the reference's *treatment* (a gradient header and rail, translucent surfaces, a glow background, a near-black dark background and a white or soft-tinted light background) but **does not use OkyAi's violet and magenta or any of its exact colors**. The proposed palette is a blue primary with a blue-to-teal gradient (plan §7.1). It is not brand approval.
- **UI-FR-9 (revised v3, owner decision 2026-10-11, supersedes Q2)** **Manrope** (`next/font/google`, same mechanism as before) is the application font. It is the closest freely available match to the reference's Satoshi, which is **not** added (no font files, no new dependency). Typography stays a centralized token (`--font-geist-sans` is the legacy variable name that now carries Manrope). Remaining differences from Satoshi are documented for review (AC-8.4).
- **UI-FR-11 (revised, owner decisions Q3 and Q5) Shell.** A header bar and a sidebar as observed:
  - **Header:** sticky, 72 px, gradient background, bottom corners rounded, inset from the content edges. Contents: the sidebar toggle (below 1280 px) and the application theme switcher. **No search, notification or user placeholders.** Only functional actions or explicitly approved elements appear. The user area returns with the authentication feature.
  - **Sidebar (v3):** at 1280 px and wider an 88 px icon rail with a vertically centred gradient navigation panel (24 px curves) and the logo tile above it; below 1280 px an off-canvas labelled drawer opened from the header. The top navbar is kept: a 72 px gradient bar with 24 px curves, brand name, a round theme-menu button and a round account-menu button (UI-only, all entries disabled until authentication exists). Every navigation item has an accessible name. All tooltips use the amber-to-pink pill with an arrow (dark text, AA). Interactive controls show the pointer cursor. The footer is a rounded-top strip. No desktop expand control, no search and no notification element.
  - **Content:** scrollable, centred container up to 1280 px, then a footer.
  - **Ambient background** layer under the content (glow), decorative only.
- **UI-FR-12 Navigation source.** Items are declared per module in a central definition, not hardcoded in pages.
- **UI-FR-13 (revised) Page structure.** Optional breadcrumb, H1 title, optional muted description, right-aligned actions with one primary action, then content in cards.
- **UI-FR-14 (revised) Shape and elevation.** Card radius 24 px, controls 8 px, navigation items 10 px, header bottom 16 px, dialogs 24 px. Cards are bordered and translucent with a very light shadow. Overlays have a stronger shadow. Values are set in the plan.
- **UI-FR-15 (revised) Density.** One density. Base spacing unit 0.28 rem. Control height 40 px. No customiser.
- **UI-FR-16 (revised) Component inventory.** v1 inventory (button, icon button, link, text input, textarea, select, checkbox, radio, switch, form field, card, badge/status, table, pagination, filter bar, tabs, dialog, drawer, dropdown menu, tooltip, toast, alert, avatar, skeleton, spinner, breadcrumb, page header, empty, error and permission-denied states) **plus**: stat card (label, value, hint, trend slot, icon tile), icon tile, card header with icon tile, toggle row (icon, title, description, switch), footer, danger card variant, gradient and outlined button variants.
- **UI-FR-17 Forms.** Always-visible labels, inline errors tied to fields, server `errors[]` mapped to fields, a pending state that blocks double submit, and consistent required/optional marking.
- **UI-FR-18 Tables.** Server-side pagination only, visible sort and filter state, per-table loading, empty and error states, and horizontal scroll inside the container on narrow screens. Table styling is **Unverified** against the reference.
- **UI-FR-19 Status.** One status-to-badge mapping, never conveyed by color alone.
- **UI-FR-20 Theme behavior (owner decision Q4).** Light, dark and **follow-system as the default**, with an application-level theme switcher. The choice persists.
- **UI-FR-21 Ownership.** Shared components live in one location decided in the plan. Features compose them and do not fork them. Promotion to shared needs approval.
- **UI-FR-22 Consistency rules.** No arbitrary colors, spacing, typography, button styles or independent navigation patterns. Exceptions need approval.
- **UI-FR-23 Boilerplate.** Replacing the create-next-app home page and metadata happened under v1 and is retained. The health-status functionality is preserved.
- **UI-FR-24 (new) Reference fidelity rules.** Where the reference's value fails an acceptance criterion (accessibility), Timely uses the nearest passing value and records the deviation. Where the reference is **Unverified**, Timely applies the same tokens and does not claim a match.
- **UI-FR-25 (new) Reduced effects.** Translucency, blur, gradients and glows are decorative and degrade to solid surfaces when the user prefers reduced transparency or forced colors, without losing information or contrast.

## 3B. Reference characteristics (summary; detail in `reference-analysis.md`)
| Class | Content |
|---|---|
| **Observed** | Rail and drawer behavior, header composition and size, card, control and navigation radii, spacing unit 0.28 rem, type sizes, token values (dark theme, and light partly), metric-card, settings-card, toggle-row and danger-zone patterns, 404 layout, glow backgrounds, footer, floating gear tab and upgrade card (not adopted) |
| **Inferred** | The 1280 px breakpoint (from class names), large-button size, icon set |
| **Unverified** | Dropdowns, dialogs, tooltips, toasts, tables, hover/focus/pressed states, notification panel, user menu, any desktop expand behavior, keyboard and screen-reader behavior, light-theme text colors in full, RTL rendering |

## 3C. Validation Approach (PROPOSED; detail in the plan)
*(Added section.)*
- **Automated:** unit tests for token completeness and **composited** contrast, navigation, theme, state mapping, pagination, toast logic and the raw-color guard, plus lint, typecheck and build, using the existing commands (no new test dependencies, PD-7 Option A).
- **Reference comparison:** a repeatable procedure that opens the Timely preview and measures the AC-8.1 and AC-8.2 values in a real browser (headless Edge, outside the repo, no new dependency), then produces side-by-side screenshots for the owner (AC-8.4).
- **Manual accessibility checklist:** keyboard-only pass, focus visibility, zoom and reflow at 320 px and 400%, and a screen-reader spot check on shell, drawer, dialog and form. Run by the owner or marked Not executed.
- Results are reported as executed only after they are run (P6).

## 4. Operations Clients Need
None. No new endpoints. The shared API client and its error mapping are reused unchanged.

## 5. Data and Ownership (business level)
- Creates no business data. It stores only non-sensitive UI preferences (theme).
- Sensitivity: low. No tokens or secrets in browser storage (P5).
- Retention/freshness: not applicable.

## 6. External Systems and Dependencies
- External systems: None.
- Depends on the existing stack and on the five packages already approved and installed under v1 (`@tabler/icons-react`, four `@radix-ui` packages).
- Depends on the existing stack and on the five packages already approved and installed under v1 (`@tabler/icons-react`, four `@radix-ui` packages). **No new dependency or font asset** is needed: Geist is kept (Q2) and the select is the styled native element (Q6).
- Official brand guidelines are DEFERRED.

## 7. Non-Functional Requirements
- Performance: no layout shift from the theme, and the shell stays server-rendered where possible. Blur and gradient effects must not make interaction janky (assessed in validation). Numeric budgets are OPEN under D-29.
- Security/permissions: no business rules or authorisation in UI, and no secrets in UI code.
- Auditability: none.
- Accessibility/i18n: WCAG 2.2 AA, measured by AC-5.x. English now. RTL and localisation are DEFERRED.

## 8. Edge Cases & Error States
Very long names and labels, large tables on mobile, session expiry mid-form (401), backend unavailable, empty datasets, zero permitted nav items, a stored dark theme on first paint, JavaScript failure, long breadcrumb trails, focus returning after dialogs and the drawer close, sticky header hiding focused elements, translucent cards over a bright light-theme glow, forced-colors mode, reduced transparency, a very tall rail panel on short viewports (many nav items), and the rail's vertical centring with more than the fitted number of items.

## 9. Out of Scope
Authentication, SSO and any functional login (the non-functional Login Page Preview is the one owner-approved exception), business dashboards, attendance, employee management, reports, functional global search, functional notifications, inert search, notification or user placeholders in the header, charts and AI features, calendars, kanban, chat, email, calls, CRM, payroll, recruitment, multi-tenant or super-admin UI, theme and layout customiser (including the reference's gear tab), alternative layouts, RTL, app-switcher dropdown, promotional or upgrade cards, new backend endpoints, copying template code, assets, illustrations or branding.

## 10. Decisions and Open Questions
**Decided by the owner on 2026-10-11** (owner-directed; they become CONFIRMED on approval of v2):

| # | Decision | Where it applies |
|---|---|---|
| Q1 | Palette: a **Timely-specific brand palette** that keeps OkyAi's gradient treatment, surface styling and visual language. OkyAi's exact brand identity and colors are not copied | UI-FR-2, plan §7.1 |
| Q2 | Font: ~~keep Geist~~ **superseded by V3-2 (Manrope, 2026-10-11)**; typography differences from the reference are documented for visual review | UI-FR-9, AC-8.4 |
| Q3 | Header: **omit** inert search and notification icons. Only functional actions or explicitly approved navigation elements | UI-FR-11, AC-8.5 |
| Q4 | Default theme: **follow the system preference**, with an application-level theme switcher | UI-FR-20 |
| Q5 | Sidebar: **accept** the desktop icon rail and responsive off-canvas drawer, **keep the top navbar**, give navigation items accessible names and tooltips where needed | UI-FR-11, AC-2.2 |
| Q6 | Select: **styled native select**, no extra dependency to imitate the reference | UI-FR-16, plan §7.4 |
| Q7 | Comparison tooling: **outside the repository** unless repeatable validation later shows a clear need to commit it | §3C, plan PD-15 |
| V3-1 | Palette: **violet ? purple ? magenta** gradient, purple-tinted near-black dark theme, lavender-tinted light theme with ambient glows. Supersedes the blue-to-teal direction of Q1. No exact OkyAi hex value is used | UI-FR-2, AC-1.1, AC-6.1 |
| V3-2 | Font: **Manrope**. No Satoshi files and no new dependency. Supersedes Q2 | UI-FR-9 |
| V3-3 | Header: 72 px bar, 24 px curves, round theme menu and a **UI-only account menu** with a placeholder identity ("Timely user") and disabled entries. Narrows Q3 and A1: still no search, notification or functional user elements | UI-FR-11, AC-8.5 |
| V3-4 | Rail 88 px, curves equal to the header (24 px), tooltips on every control share one amber-to-pink style (dark text for AA), pointer cursor on interactive controls, rounded-top footer | UI-FR-11, UI-FR-14, UI-FR-16 |
| V3-5 | Form controls follow the reference's Content Tools inputs (40 px, 8 px radius, faint border, optional leading icon). Only the search input and list were observable without login; other controls remain unverified against the reference | UI-FR-16, AC-8.4 |

**Interpretation to confirm at review (A1):** the owner's Q3 ("only functional actions") is applied to the static user avatar as well, because it is non-functional. The header therefore holds only the sidebar toggle (below 1280 px) and the theme switcher. The user area returns with the authentication feature. This leaves the header visibly sparser than the reference. If you want an avatar or other element kept, say so before approval.

**Open:** none that blocks approval.
- **DEFERRED:** official brand palette, logo and typography, RTL and localisation, alternative layouts and customiser, functional search and notifications, numeric performance budgets (D-29).
- **Left to the plan (PROPOSED):** exact token values, shell construction, background glow implementation.

## 11. Change Log
Changes after approval require re-approval (see `docs/sdd-workflow.md` §5).

| Date | Change | Reason | Approved by |
|---|---|---|---|
| 2026-10-11 | v1: initial approval of the spec (draft v3, SmartHR reference) | Owner approval (`SPEC APPROVED`) | Project owner |
| 2026-10-11 | v2: OkyAi replaces SmartHR as the primary reference with a close-visual-match target. Added US-8 and AC-8.1 to AC-8.5, revised AC-2.1, AC-2.2, AC-4.1, AC-5.1, AC-5.3 and UI-FR-1, 2, 6, 9, 11, 13 to 16, 20, added UI-FR-24 and 25, new open questions Q1 to Q7, expanded edge cases and out-of-scope items | Owner request (`CHANGES REQUESTED`, 2026-10-11) | Pending owner |
| 2026-10-11 | v2 approved by the owner (A1 confirmed). **Owner-directed scope addition:** a Login Page Preview at `/ui-preview/login`, a visual prototype only (no authentication, SSO, session, storage or API call), non-production. This relaxes §9 "login screens" for that single prototype page | Owner instruction (2026-10-11) | Project owner |
| 2026-10-11 | v2 (decisions recorded): Q1 Timely-specific palette, Q2 Geist kept, Q3 header placeholders omitted, Q4 follow-system default, Q5 rail and drawer accepted with the top navbar kept, Q6 styled native select, Q7 comparison tooling outside the repo. Revised UI-FR-2, 9, 11, 20, AC-8.4, AC-8.5, §6, §9 and §10. Added interpretation A1 (avatar also omitted) | Owner decisions (2026-10-11) | Pending owner |
| 2026-10-11 | **v3 visual correction, approved by the owner after reviewing the implementation screenshots:** V3-1 to V3-5 above. Revised UI-FR-2, UI-FR-9, UI-FR-11, AC-8.1 and the decision table | Owner review (2026-10-11) | Project owner |

---
**Status:** Approved · **Approved by:** Project owner · **Date:** 2026-10-11 · **Linked constitution:** `docs/constitution.md` (v1.1) · **Supersedes:** v1 (approved 2026-10-11)
