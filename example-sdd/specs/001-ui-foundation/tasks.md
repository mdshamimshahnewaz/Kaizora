# Task Breakdown — UI Foundation (v2)

> **Purpose:** Break the `plan.md` v2 into small, ordered, independently verifiable tasks, each with a pass/fail condition.
> **Location:** `specs/001-ui-foundation/tasks.md`.
> **Version:** v2, rebuilt after the owner's `CHANGES REQUESTED` (2026-10-11). **Status: Ready for approval.** v1's approval and its "Implementation authorised" record do **not** carry over. Implementation starts only after the owner approves spec, plan and this list **and** gives a separate explicit `IMPLEMENT` instruction (`docs/decisions.md` D-6).
> **Scope guard:** all tasks are inside `frontend/` plus the docs named in T21, and `specs/` records. No backend, Django API, database, package install or Constitution change. The five v1-approved packages stay as they are. Any new dependency or asset needs separate approval (plan §8.1).

## Conventions
- `[ ]` pending, `[x]` done, `[~]` in progress, `[!]` blocked (explain why).
- Each task references the plan section and spec item it implements. The list order is the execution order.
- Every task that adds logic adds its automated test in the same task (`node:test`, no new test dependencies, plan PD-7 Option A).
- Executed results are recorded only in `validation.md` (P6). Reference screenshots are not committed.
- Before writing any Next.js code, read the relevant guide in `frontend/node_modules/next/dist/docs/` (`frontend/AGENTS.md`).
- **Baseline:** the v1 implementation is in the working tree (uncommitted). Tasks below change it. Retained logic and tests must keep passing.

## Decisions (owner, recorded 2026-10-11, no longer prerequisites)
| ID | Decision | Applies to |
|---|---|---|
| Q1 | Timely-specific palette with none of OkyAi's exact colors. **Direction superseded 2026-10-11: violet → purple → magenta** (T27) | T2, T3, T27 |
| Q2 | ~~Geist kept~~ **Superseded 2026-10-11: Manrope** (no Satoshi files, no new dependency). Differences are documented | T2, T24, T31 |
| Q3 | No inert search, notification or user elements in the header. Only functional actions | T6 |
| Q4 | Follow the system theme by default, with an application-level switcher | T4, T6 |
| Q5 | Desktop icon rail and responsive drawer accepted, top navbar kept, accessible names and tooltips | T6, T7, T8, T9 |
| Q6 | Styled native select, no extra dependency | T13 |
| Q7 | Comparison tooling stays outside the repo unless repeatable validation shows a clear need | T23, T24 |

Open item to confirm at review: **A1**, that the static user avatar is also omitted from the header (spec §10).

## A. Baseline
- [x] **T1 — Confirm the baseline** _(depends on: none)_
  - Implements: Plan §2.1, §10
  - Done when: `npm run lint`, `npm run typecheck`, `npm test` and `npm run build` pass on the current tree before any change, `package.json` and `package-lock.json` are unchanged by v2, and the results are noted in `validation.md` as the starting point.

## B. Tokens, brand, navigation
- [x] **T2 — Rewrite tokens and base styles** _(depends on: T1)_
  - Implements: Plan §7.1, §7.2, PD-1, PD-13; Spec UI-FR-2, UI-FR-3, UI-FR-9, UI-FR-14, UI-FR-15, UI-FR-25, AC-1.1, AC-4.1, AC-5.3, AC-8.2, AC-8.3
  - Do: in `app/globals.css`, define the v2 role set for light and dark using the **Timely-specific blue-to-teal palette** in plan §7.1 (translucent surfaces, opaque `surface-raised`, `primary-text`, gradient stops, `rail-fg`, glow tokens, `border-strong`, `focus-ring`, status colors), map them with `@theme inline`, set `--spacing: 0.28rem`, the radius tokens, the type scale (30/36, 18/28, 16/24, 14/20, 12/16, metric 30/36), the card shadow, gradient, glass and glow utilities, a base focus ring, and the reduced-motion, reduced-transparency and forced-colors fallbacks. Geist stays through the existing font setup.
  - Done when: every role exists in both themes, no value equals an OkyAi color, utilities such as `bg-surface`, `text-fg-muted`, `bg-linear-to-r from-gradient-start to-gradient-end` compile in a build, no raw palette colors exist outside `globals.css`, and the page renders with the new type and spacing without layout errors.
- [x] **T3 — Composited contrast and completeness test** _(depends on: T2)_
  - Implements: Plan §10, PD-11; Spec AC-5.3, AC-5.4, AC-4.1, AC-6.1, AC-8.3
  - Done when: `tests/tokens.test.mjs` is rewritten to composite translucent surfaces over `canvas` and `glow-peak` in sRGB, checks every listed pair at 4.5:1 (text) or 3:1 (UI, icons, focus) in both themes, including white on both gradient stops, drawer labels, `rail-fg`, `primary-text`, status colors, `border-strong` and `focus-ring`, and passes. It fails if any pair or role is missing.
- [x] **T4 — Brand, navigation rendering rules and theme default** _(depends on: T2)_
  - Implements: Plan §4, §7.5; Spec UI-FR-12, UI-FR-20, AC-2.1 to AC-2.3, AC-6.1
  - Do: `lib/brand.ts` gains the footer name. `lib/navigation.ts` keeps its contract and gains a helper that decides whether group titles are shown (more than one group). `components/ui/icon.tsx` gains any icons the new shell needs. The theme default stays follow-system (Q4), so `lib/theme.ts` and its script are unchanged apart from anything the switcher needs.
  - Done when: existing navigation and theme tests still pass, new tests cover the group-title helper and the chosen theme default, and the pre-paint script still agrees with the resolver in the VM test.

## C. Shell
- [x] **T5 — Ambient glow layer** _(depends on: T2)_
  - Implements: Plan §7.3; Spec UI-FR-11, UI-FR-25, AC-4.1
  - Done when: a decorative fixed layer (`aria-hidden`, `pointer-events-none`) renders the glow in both themes, caps its intensity at the token peaks, and disappears under `prefers-reduced-transparency` and `forced-colors`.
- [x] **T6 — Header** _(depends on: T2, T4)_
  - Implements: Plan §7.3, PD-14; Spec UI-FR-11, AC-5.4, AC-8.1
  - Done when: a sticky 72 px gradient header with 16 px bottom corners and the specified inset contains **only** the sidebar toggle (below 1280 px) and the compact three-choice theme switcher (light, dark, system). There is no search, notification, avatar or other inert element, and no authentication behavior. Text and icons on the gradient meet contrast. Sticky regions do not obscure focus.
- [x] **T7 — Desktop rail** _(depends on: T2, T4)_
  - Implements: Plan §7.3, PD-12; Spec UI-FR-11, AC-2.2, AC-5.5, AC-8.1
  - Done when: at 1280 px and wider a fixed 96 px rail shows the logo above a vertically centred gradient panel with 56×47 px items (10 px radius), a visible active state plus `aria-current="page"`, Radix tooltips and programmatic names, nested groups opening in a menu, and the panel scrolling inside itself when taller than the viewport. Concave joins are drawn with CSS only. No copied asset.
- [x] **T8 — Navigation drawer** _(depends on: T7, T6)_
  - Implements: Plan §7.3; Spec UI-FR-11, AC-2.2, AC-5.2
  - Done when: below 1280 px the header toggle opens a Radix drawer with the gradient, wordmark, icon-and-label items at full-strength white, group titles only when there is more than one group, and nothing promotional. The drawer closes on navigation, traps and restores focus, and closes with Esc.
- [x] **T9 — Footer, content container and shell assembly** _(depends on: T5, T6, T7, T8)_
  - Implements: Plan §7.3; Spec UI-FR-11, AC-2.1, AC-5.1, AC-5.6
  - Done when: the shell has the skip link, rail `aside`, `header`, `main` and a footer card, the content container is centred at up to 1280 px, the v1 collapsible 256 px sidebar and its toggle are removed, the build output still shows `/` as a partial prerender, and no horizontal page scroll occurs at 320, 390, 768, 1024, 1280 and 1440 px.
- [x] **T10 — Page header and breadcrumbs** _(depends on: T2)_
  - Implements: Plan §7.3; Spec UI-FR-13, AC-2.1, AC-8.3
  - Done when: a quiet breadcrumb line (labelled `nav`, `aria-current` on the last item), one H1 at 30/36 bold, an optional 16/24 lead text and a right-aligned actions area render, with the layout wrapping cleanly on narrow screens.

## D. Shared components (`components/ui/`)
- [x] **T11 — Cards, icon tile, stat card, toggle row** _(depends on: T2, T4)_
  - Implements: Plan §7.4; Spec UI-FR-14, UI-FR-16, AC-8.2
  - Done when: `Card` is translucent with 24 px radius, 1 px border and about 27 px padding, `CardHeader` accepts an `icon` and renders an `IconTile`, `StatCard` renders label, value, hint, a trend slot (icon, signed percent and text, never color alone) and an icon tile, `ToggleRow` renders icon tile, title, description and the switch, and a danger variant exists. None contains product data or charts.
- [x] **T12 — Buttons and links** _(depends on: T2)_
  - Implements: Plan §7.4; Spec UI-FR-16, AC-5.5, AC-8.2
  - Done when: primary (gradient, white text at 4.5:1 or better), outlined secondary, outlined destructive, ghost and large call-to-action variants exist, pending state still blocks double submit, icon buttons still require a label, and all are at least 24 px with visible focus.
- [x] **T13 — Form controls** _(depends on: T2, T12)_
  - Implements: Plan §7.4; Spec UI-FR-16, UI-FR-17, AC-5.5, AC-5.6, AC-8.2
  - Done when: input, textarea, select (styled native element with an overlaid chevron, Q6; no new dependency), checkbox, radio, switch and `FormField` follow the 40 px height, 8 px radius, translucent fill and `border-strong`, keep label, hint, error, `aria-describedby`, `aria-invalid` and required/optional marking, and the pending read-only behavior.
- [x] **T14 — Overlays** _(depends on: T2, T12)_
  - Implements: Plan §7.4; Spec UI-FR-8, AC-5.2, AC-5.4
  - Done when: dialog, drawer, dropdown menu, tooltip and tabs use the new tokens with opaque `surface-raised` for overlays, keep the Radix behavior (focus trap and restore, Esc, arrow keys), and keep labelled close controls.
- [x] **T15 — Feedback components** _(depends on: T2, T12)_
  - Implements: Plan §7.4; Spec UI-FR-16, UI-FR-19, AC-3.3
  - Done when: badge (single status map, text and icon), alert, avatar, skeleton, spinner and toast use the new tokens, toast logic tests still pass, and the live regions (polite status, assertive alert) are unchanged.
- [x] **T16 — State cards** _(depends on: T4, T11, T12)_
  - Implements: Plan §7.4; Spec US-3, AC-3.1, AC-3.2
  - Done when: `LoadingState`, `EmptyState`, `ErrorState` and `PermissionDeniedState` use a centred state-card layout (own icon, heading, text, actions, optional `request_id`) and still take their content from `describeError` and never render raw error text.
- [x] **T17 — Table, pagination, filter bar** _(depends on: T12, T13, T16)_
  - Implements: Plan §7.4, PD-8; Spec UI-FR-18, AC-5.1, AC-5.7
  - Done when: they use the new tokens, keep the labelled focusable scroll container, sticky first column, `aria-sort`, envelope-driven pagination and active-filter chips, and the existing pagination tests pass. Their look is recorded as Unverified against the reference.

## E. Pages
- [x] **T18 — Home page and health status re-skin** _(depends on: T9, T10, T11)_
  - Implements: Plan §7.6; Spec UI-FR-23
  - Done when: `app/page.tsx` still renders inside the shell with the page header and the unchanged `<HealthStatus />` inside its `Suspense` boundary, `health-status.tsx` logic, roles and text are unchanged (only token classes), and `lib/api/client.ts` and its tests are untouched.
- [x] **T19 — Preview compositions** _(depends on: T11 to T17, T18)_
  - Implements: Plan PD-6, §10; Spec AC-5.x, AC-8.4
  - Done when: `app/ui-preview/page.tsx` (still `notFound()` in production and listed in no navigation) renders every component and state in both themes plus two reference-style compositions: a metric-card dashboard layout (stat cards in a four-column grid, large cards in a two-column split, no charts) and a settings-style layout (icon-tile cards, form fields, toggle rows, a danger card).

## F. Guard rails and docs
- [x] **T20 — Extend the raw-color guard** _(depends on: T2, T9 to T19)_
  - Implements: Plan PD-9; Spec AC-1.1, UI-FR-22
  - Done when: `tests/raw-colors.test.mjs` also fails on palette names inside gradient utilities and passes on the finished code.
- [x] **T21 — Update UI rules docs** _(depends on: T2, T9)_
  - Implements: Plan PD-10; Spec UI-FR-21, UI-FR-22, UI-FR-24, AC-7.1
  - Done when: `docs/frontend-ui-rules.md` states the v2 rules (token-only styling, the OkyAi-based look, the rail and drawer contract, the AA deviation rule, the glass and reduced-effects rule, ownership and exceptions). `docs/tech-stack.md` is unchanged (no new dependency). Both stay PROPOSED unless the owner confirms.

## G. Validation
- [x] **T22 — Run the full automated suite** _(depends on: T1 to T21)_
  - Implements: Plan §10; Spec AC-1.1 to AC-6.1
  - Done when: `npm run lint`, `npm run typecheck`, `npm test` and `npm run build` pass, the generated CSS contains the token and gradient utilities, and `/` is still a partial prerender. Results are recorded with command output in `validation.md`.
- [x] **T23 — Reference measurement** _(depends on: T22)_
  - Implements: Plan §10, PD-15; Spec AC-8.1, AC-8.2, AC-8.3
  - Done when: computed styles are read in a real browser from the Timely preview at 1440, 1280, 1024, 768 and 390 px and compared with the observed values (header 72 px and 16 px bottom radius, rail 96 px, item 56×47 px and 10 px radius, container 1280 px, card radius 24 px and padding, control height 40 px and radius 8 px, type sizes) within ±2 px. A results table with pass or deviation per value goes in `validation.md`. Nothing is committed (Q7). If repeating the measurement proves valuable, committing the script is raised separately as new tooling.
- [x] **T24 — Side-by-side visual comparison** _(depends on: T23)_
  - Implements: Plan §10; Spec AC-8.4, AC-8.5
  - Done when: side-by-side screenshots (reference and Timely) of the dashboard-style and settings-style compositions at 1440, 1024, 768 and 390 px in both themes are produced and shown to the owner, every AA-driven deviation is listed (plan §7.1), **the Geist-versus-reference typography differences are listed**, Unverified items carry no match claim, and **the owner's accept or change decision is recorded**. Reference images are not committed.
- [x] **T25 (closed with limitations 2026-10-11; partly executed: scripted browser checks run; screen-reader and real touch checks are for the owner) — Manual accessibility and responsive pass** _(depends on: T22)_
  - Implements: Plan §10; Spec AC-5.1 to AC-5.7, AC-4.1
  - Done when: the checklist in `validation.md` is executed on `ui-preview` and the home page in both themes at 320, 390, 768, 1024, 1280 and 1440 px plus 400% zoom: keyboard-only pass, focus visible and not obscured, touch targets, reduced motion, reduced transparency, forced colors, and a screen-reader spot check (rail, drawer, dialog, form, toast). **Checks that need a real screen reader or touch device are run by the owner or marked Not executed.** They are never marked Passed without evidence (P6).
- [x] **T26 — Validation record v2** _(depends on: T22 to T25)_
  - Produces: `specs/001-ui-foundation/validation.md` from `sdd-templates/validation-checklist-template.md`
  - Done when: every AC is Passed (with executed evidence) or explicitly Deferred or Not executed with a reason, planned and executed results are separate, the v1 results are marked superseded, and the document is marked `Ready for approval`.

## H. Visual correction v3 (owner review, 2026-10-11; supersedes the blue-to-teal values in T2, T3, T7 and the 96 px rail)
- [x] **T27 — Violet-to-magenta tokens** _(done: `globals.css`, `tests/tokens.test.mjs` updated; 47 tests pass)_
  - Done when: both themes use the violet → purple → magenta gradient (`gradient-mid` added), the purple-tinted dark and lavender-tinted light canvases and surfaces, and `tokens.test.mjs` verifies AA contrast, the hue range and no OkyAi hex value.
- [x] **T28 — Shell, header, rail, page header and Home re-skin** _(done: verified by screenshots and computed styles, see `validation.md` §2.5)_
  - Done when: header 72 px with 24 px bottom corners, brand gutter and logo tile, 88 px rail with elliptical concave fillets and a 144 px content offset, labelled drawer below 1280 px, fluid content aligned to the header, shared card, button and input radii, a restyled health panel with an icon and a functional "Check again" action, and no inert controls.
- [x] **T31 — Header menus, shared tooltips, cursor, footer, curves, background, Manrope** _(done 2026-10-11: `theme-toggle.tsx`, `profile-menu.tsx`, `tooltip.tsx`, `dropdown-menu.tsx`, `globals.css`, `app-shell.tsx`, `layout.tsx`; verified in `validation.md` §2.6)_
  - Done when: round theme and account menus size to their items, every tooltip uses one style, interactive controls show the pointer cursor, header and rail share one 24 px antialiased curve, the footer is a rounded-top strip, both themes use layered glows, the font is Manrope with no new asset or dependency, and lint, typecheck, tests and build pass.
- [x] **T29 — Re-run automated checks and capture screenshots** _(done: lint, typecheck, test, build; screenshots at 1440, 1024 and 390 px in both themes)_
- [x] **T30 — Owner accepts the v3 visual comparison** _(done: owner approved the corner and background changes on 2026-10-11, conditional on the final screenshots; they are recorded in `validation.md` §2.6)_

> Feature closed 2026-10-11. The Not-executed manual checks (screen reader, real touch, 400% zoom, real-keyboard tooltip focus) are recorded as limitations in `validation.md` §6 and are not marked passed.

## Traceability
| Plan item | Tasks |
|---|---|
| §7.1 tokens, PD-1, PD-11 | T2, T3 |
| §7.2 type, shape, spacing, PD-13 | T2 |
| §7.3 shell, PD-12, PD-14 | T5 to T10 |
| §7.4 components and states | T11 to T17 |
| §7.5 theme | T4 |
| §7.6, PD-6 boilerplate and preview | T18, T19 |
| §8.1 dependencies (none new) | T1, T22 |
| PD-9 raw-color guard | T20 |
| PD-10 docs | T21 |
| §10, PD-15 testing and comparison | T3, T22 to T26 |

| Spec item | Tasks |
|---|---|
| US-1, AC-1.1, AC-1.2 | T2, T11 to T17, T20 |
| US-2, AC-2.1 to AC-2.3 | T4, T7 to T10 |
| US-3, AC-3.1 to AC-3.3 | T15, T16, T17 |
| US-4, AC-4.1 | T2, T3, T4, T5 |
| US-5, AC-5.1 to AC-5.7 | T2, T3, T6 to T9, T12 to T17, T25 |
| US-6, AC-6.1 | T2, T3, T4 |
| US-7, AC-7.1 | T20, T21 |
| US-8, AC-8.1 | T6, T7, T8, T9, T23 |
| AC-8.2, AC-8.3 | T2, T10 to T13, T23 |
| AC-8.4 | T19, T24 |
| AC-8.5 | T7, T8, T19, T24 |
| UI-FR-24, UI-FR-25 | T2, T5, T21 |

## Notes
- Out of scope (spec §9): authentication, login, business pages, functional search or notifications, charts, layout variants, RTL, the customiser tab, promotional cards, new backend endpoints.
- The shared API client, `HealthStatus` behavior and `API_URL` handling must not change.
- Split any task that grows too large, and raise any work outside the approved plan for approval.

## Change Log
Changes after approval require re-approval and pause implementation (see `docs/sdd-workflow.md` §5).

| Date | Change | Reason | Approved by |
|---|---|---|---|
| 2026-10-11 | v1: initial approval of the task list (T1 to T23, SmartHR reference) and implementation authorised | Owner (`TASKS APPROVED`, `IMPLEMENT`) | Project owner |
| 2026-10-11 | v2: rebuilt as T1 to T26 for the OkyAi reference, with prerequisite decisions Q1 to Q7, reference measurement and visual comparison tasks. The v1 implementation authorisation is withdrawn pending approval | Owner request (`CHANGES REQUESTED`, 2026-10-11) | Pending owner |
| 2026-10-11 | v2 approved, implementation authorised; Login Page Preview (visual prototype, no authentication) added to scope by the owner | Owner (`APPROVED`, 2026-10-11) | Project owner |`n| 2026-10-11 | v2 (decisions recorded): Q1 to Q7 are decided, so they are no longer prerequisites and the dependency notes were removed. T2 uses the Timely-specific palette, T6 has no placeholders, T13 uses the native select, T23 and T24 updated | Owner decisions (2026-10-11) | Pending owner |

---
**Status:** Approved · **Approved by:** Project owner · **Date:** 2026-10-11 · **Implementation authorised by owner:** Yes (2026-10-11, `IMPLEMENT` after approval of v2) · **Supersedes:** v1 (approved 2026-10-11)
