# Technical Plan — UI Foundation (v2)

> **Purpose:** HOW the approved-on-v2 `spec.md` will be implemented. Every decision traces to a spec item.
> **Location:** `specs/001-ui-foundation/plan.md`. **Rules:** `docs/constitution.md`, `docs/architecture.md`, `docs/api-conventions.md`, `docs/frontend-api-client.md`.
> **Version:** v2, a revision of the approved v1 after the owner's `CHANGES REQUESTED` (2026-10-11). **Status: Approved (2026-10-11).**
> **Status labels:** CONFIRMED, PROPOSED, OPEN, DEFERRED. Nothing in this plan is CONFIRMED until the owner approves it, except decisions the owner already made on 2026-10-11 (Q1 to Q7, marked below), which become CONFIRMED on approval of v2. Dependencies approved under v1 remain approved. **No new dependency is proposed in v2** (§8.1).
> **Evidence base (read-only, 2026-10-11):** `specs/001-ui-foundation/reference-analysis.md` (v2: rendered screenshots, computed styles and shipped tokens of the OkyAi dashboard), the current `frontend/` working tree (v1 implementation, uncommitted), `specs/001-ui-foundation/validation.md` (v1 results), Next.js 16.4.0 docs read in v1. Contrast values below were computed on 2026-10-11 (WCAG 2 formula, alpha blended in sRGB like a browser) and are **planned evidence only**, to be re-proven by tests.

## 1. Linked Spec
Source: `specs/001-ui-foundation/spec.md` v2 · Covers: US-1 to US-8, AC-1.1 to AC-8.5, UI-FR-1 to UI-FR-25.

## 2. Architecture Overview
- **Frontend only**, unchanged in kind. No Django module, endpoint, model or migration. Presentation only (AR-1, P8). The only backend call remains the existing health check through `lib/api/client.ts`.
- **Layers (unchanged from v1):** (1) tokens and brand, (2) shared components in `components/ui/` composed by `components/shell/`, (3) navigation definition in `lib/navigation.ts`, (4) theme in `lib/theme.ts`, (5) feature pages that only compose.
- **Rendering model (unchanged):** `cacheComponents` is on, so the root layout does not read `cookies()`. Theme is applied by an inline pre-paint script. Client components sit under `"use client"` boundaries.
- **Module/domain ownership (AR-11 to AR-14):** dependencies on other modules: **None**. Public interfaces: the `lib/navigation.ts` contract and `components/ui` exports. Data ownership: none. Client API parity: no new APIs.

### 2.1 Disposition of the existing v1 implementation
The v1 implementation exists in the working tree (uncommitted, built under the v1 plan). v2 changes its look and shell. It does not restart from scratch.

| Area | v2 treatment |
|---|---|
| `lib/theme.ts`, `lib/navigation.ts`, `lib/brand.ts`, `lib/cn.ts`, `components/ui/states/error-map.ts`, `status-map.ts`, `pagination-logic.ts`, `toast-logic.ts`, `icon.tsx` | **Retained.** Small edits only (navigation gains per-surface rendering rules, brand gains a footer name, icon registry gains a few icons) |
| Their tests, `tests/api-client.test.mjs`, `tests/raw-colors.test.mjs`, `tests/theme.test.mjs`, `tests/navigation.test.mjs`, `tests/ui-logic.test.mjs` | **Retained**, extended where behavior changes |
| `app/globals.css` and `tests/tokens.test.mjs` | **Rewritten** (new token set, composited-contrast test) |
| `components/shell/*` (sidebar, app shell, header, page header) | **Rewritten** to the OkyAi composition (rail, drawer, gradient header, footer, glow) |
| `components/ui/*` visuals | **Restyled** to the new tokens. Public props stay stable where possible. Added: stat card, icon tile, icon-tile card header, toggle row, danger card variant, gradient button |
| `app/page.tsx`, `app/health-status.tsx`, `app/ui-preview/*` | **Retained and re-skinned.** Health-status logic, roles and text unchanged. The preview gains the reference-style compositions |
| The v1 expanded 256 px collapsible sidebar and its collapse toggle | **Removed** (replaced by rail and drawer, Q5) |
| Installed packages (five, v1-approved) | **Retained.** None added or removed |

### 2.2 File layout (PROPOSED; changes from v1 only)
```
frontend/
  app/globals.css            tokens v2 (both themes), @theme inline, glass/glow/gradient utilities, base styles
  components/shell/          app-shell, rail (sidebar-rail), drawer-nav, header, footer, page-header, breadcrumbs, ambient-glow
  components/ui/             + stat-card, icon-tile, toggle-row, state-card (error/denied/empty card layout)
  tests/tokens.test.mjs      composited contrast and completeness
```

## 3. Data Model and Ownership
None. Only the non-sensitive `theme` cookie is stored client-side. Sidebar state is not persisted (there is no desktop collapse, Q5).

## 4. API Contract
**No endpoints added or changed.** Internal interfaces:
```
lib/navigation.ts      unchanged contract (NavItem, NavGroup, navigation, validateNavigation, visibleNavigation, isActivePath).
                       Rendering rules: the rail shows icons only (names via tooltip and programmatic label);
                       the drawer shows icon + label, and group titles only when there is more than one group.
lib/brand.ts           { name, tagline, mark } + footer name. Provisional placeholders. No OkyAi assets.
components/ui/*        typed components. Variants use semantic tokens only.
```
Error mapping for states reuses the retained `describeError` helper. The shared client is unchanged (see v1 validation finding on missing `status` and `request_id` fields).

## 5. Security
Unchanged from v1 (no client-side authorisation, safe error states, only the `theme` cookie, inline-script CSP risk noted). No third-party images or fonts are loaded at runtime from OkyAi. New: decorative effects do not add scripts or external requests.

## 6. External Systems and Adapters
None. Fonts continue through `next/font/google` (Geist, kept by owner decision Q2). No font asset is added.

## 7. Frontend

### 7.1 Design tokens v2 (UI-FR-2, UI-FR-3, UI-FR-14, UI-FR-15, AC-1.1, AC-6.1, AC-5.3)
Same semantic roles as v1 (`canvas`, `surface`, `surface-raised`, `surface-muted`, `fg`, `fg-muted`, `fg-inverse`, `border`, `border-strong`, `primary`, `primary-fg`, `secondary`, `secondary-fg`, `success`, `warning`, `danger`, `info`, `focus-ring`, `scrim`) plus new roles: `primary-text`, `gradient-start`, `gradient-end`, `gradient-button-end`, `rail-fg`, `glow-1`, `glow-2`, `glow-peak` (the worst-case backdrop used by tests). Defined for light and dark under `:root` and `[data-theme="dark"]`, exposed with `@theme inline`. Components use only these.

**v3 correction (2026-10-11, owner review of the implementation): the blue-to-teal palette below is SUPERSEDED.** It was too far from the reference. Tokens now use a vivid violet → purple → magenta gradient (`gradient-start #7238ea`, new `gradient-mid #a02fe0`, `gradient-end #c026d3`; white on each ≥ 4.5:1, enforced by `tests/tokens.test.mjs`), a purple-tinted near-black dark canvas (`#09071a`) with purple-tinted translucent surfaces, and a soft lavender-tinted light canvas (`#f7f5fc`) with white surfaces. Still no exact OkyAi hex value. Shell dimensions also changed: rail 88 px (was 96), header and content left offset 144 px (`--shell-left`, rail column plus brand gutter), right margin 48 px, header 72 px with 24 px bottom corners and a logo tile in the left gutter, rail fillets rebuilt as full-width elliptical concave curves, fluid content width. The table and values in this section describe v2 and are kept only for history; `app/globals.css` is the source of truth. AA-driven deviations in v3: gradient end `#c026d3` (4.7:1 with white) is deeper than the reference's lighter magenta, dark `primary-text` is a light violet instead of the brand violet, borders on controls use `border-strong`, status colors use the AA-tuned values.

**Provisional Timely palette (v2, superseded; PROPOSED, not brand approval; owner decision Q1).** The palette is **Timely-specific**: a blue primary with a blue-to-teal gradient. It keeps the reference's gradient treatment and surface styling but shares **none** of OkyAi's colors (the reference is violet to magenta). Values were computed on 2026-10-11 and are to be re-proven by tests.

| Role | Dark | Light | Contrast (planned) |
|---|---|---|---|
| `canvas` | `#050a17` | `#ffffff` | Base page color |
| `surface` (cards) | white 6% | white 40% | Translucent with a backdrop blur. Composites to `#141925` (dark) and `#ffffff` (light) over `canvas`, and to `#1d3052` and `#e6eef7` over the glow peak |
| `surface-raised` (dialogs, menus, tooltips) | opaque `#111a2e` | opaque `#ffffff` | Opaque so overlay contrast never depends on what is underneath |
| `fg` / `fg-muted` | `#f8fafc` / `#94a3b8` | `#0b1220` / `#475569` | `fg` 12.5 to 18.9:1 (dark), 16.0 to 18.7:1 (light). `fg-muted` 5.1 to 7.7:1 (dark), 6.5 to 7.6:1 (light) |
| `primary` / `primary-fg` | `#2563eb` / `#ffffff` | same | White on primary 5.17:1 |
| `primary-text` (links, text on surfaces) | `#60a5fa` | `#1d4ed8` | 5.2 to 7.8:1 (dark), 5.7 to 6.7:1 (light) |
| `gradient-start` / `gradient-end` (header, rail, drawer, primary button) | `#2563eb` / `#0e7490` | same | White on start 5.17:1, on end 5.36:1, at the midpoint 5.38:1 |
| `rail-fg` (inactive rail icons) | white 80% | white 80% | 3.9 to 4.0:1 (icons need 3:1). Drawer **labels** use full white (5.2 to 5.4:1) |
| `border` (decorative card edge) | white 12% | ink 10% | Decorative only, about 1.2 to 1.4:1. Never relied on to identify a control |
| `border-strong` (inputs, outlined buttons) | `#94a3b8` | `#64748b` | 5.1 to 7.7:1 (dark), 4.1 to 4.8:1 (light). Needs 3:1 |
| `focus-ring` | `#93c5fd` | `#1d4ed8` | 7.3 to 11.0:1 (dark), 5.7 to 6.7:1 (light). Needs 3:1 |
| `success` / `warning` / `danger` / `info` text | `#4ade80` / `#fbbf24` / `#f87171` / `#38bdf8` | `#166534` / `#92400e` / `#b91c1c` / `#075985` | 4.7 to 11.8:1 (dark, lowest is danger over the glow peak), 5.5 to 7.6:1 (light) |
| `glow-1` / `glow-2` / `glow-peak` | blue and teal glows at about 20% alpha, peak `#0f2347` | soft sky and teal glows, peak `#d6e2f1` | Peaks are design assumptions. The glow intensity is capped at them, and tests use them as the worst-case backdrop |

**Differences from the reference that WCAG 2.2 AA requires.** These are visible and are listed in the review and in `validation.md` (AC-5.3, UI-FR-24):

| Reference value | Problem | Timely value |
|---|---|---|
| White text on the gradient end `#c425e4` (4.44:1) | Below 4.5:1 | Gradient end `#0e7490` (5.36:1). The gradient is also darker overall |
| Inactive navigation labels at about 60% white (about 3.0 to 3.2:1) | Text below 4.5:1 | Drawer labels at full-strength white. The active item is shown by fill, border and `aria-current` |
| Violet primary as text on dark (4.05:1) | Below 4.5:1 | A separate lighter `primary-text` token (5.2 to 7.8:1) |
| Input and card borders at white 12% (about 1.4:1) | Input boundary below 3:1 | `border-strong` on controls. The 12% border stays on cards as a decoration |
| Neutral grey focus ring (unmeasured) | Not shown to meet 3:1 | An explicit high-contrast `focus-ring` token |
| Translucent popovers and dialogs (unverified) | Contrast depends on the backdrop | Opaque `surface-raised` |
| Placeholder and muted text at about 50% alpha | Light theme about 4:1 | Solid `fg-muted` tokens (6.5 to 7.6:1 light) |
| Button gradient end (purple-500, about 3.9:1 with white) | Below 4.5:1 | Same end stop as the header (`#0e7490`, 5.36:1) |

**Contrast method (PD-11).** The token test composites translucent surfaces over `canvas` and over the `glow-peak` backdrop, then checks every listed foreground/background pair at 4.5:1 (text), or 3:1 (UI boundaries, icons, focus). The composite is blended in sRGB as browsers do.

### 7.2 Typography, shape, spacing, density (UI-FR-9, UI-FR-14, UI-FR-15, AC-8.2, AC-8.3)
- **Spacing:** `--spacing: 0.28rem` (the reference's unit). All Tailwind spacing utilities scale with it. v1 components that use spacing utilities scale automatically and are checked for regressions.
- **Radius:** `--radius-card: 24px`, `--radius-control: 8px`, `--radius-nav: 10px`, `--radius-header: 16px` (bottom corners), `--radius-dialog: 24px` (matches cards because dialogs are **Unverified**).
- **Elevation:** cards use `0 1px 3px` at low alpha. Overlays use the existing `shadow-overlay`.
- **Type scale:** page title 30/36 bold; section/card title 18/28 semibold; lead (page description) 16/24; body and controls 14/20; label 12/16 uppercase with tracking; metric value 30/36 bold. Replaces v1's 24/32 title. Font: **Geist** through the existing `next/font` variable (owner decision Q2). Differences from the reference's Satoshi are documented in `reference-analysis.md` §7 and shown in the side-by-side review (AC-8.4), not eliminated.
- **Density:** controls 40 px high (`h-9` at the new unit is 40.3 px), pointer targets always at least 24 px.

### 7.3 Shell (UI-FR-11 to UI-FR-13, UI-FR-25, AC-2.x, AC-8.1)
Built from CSS and Tailwind only. No copied markup or assets.
- **Header (v3):** `sticky top-0`, 72 px (`h-16`), full width of the content column (left offset 144 px at ? 1280 px). Gradient bar (`.gradient-bar`, violet ? purple ? magenta) with convex bottom corners and concave top-end fillets, all 24 px (`--curve`), drawn with CSS only (`.header-bar`, border-radius plus a clipped `box-shadow` ring so the edge is antialiased). Left: drawer toggle (below 1280 px), brand name and tagline. Right: a round theme-menu button (frosted Radix menu: Light, Dark, Follow system, check mark on the selected one) and a round UI-only account menu (placeholder identity, Profile, Settings, Help & Support and Log out, all disabled until authentication exists). **No search, no notification, no functional user elements.** White text and icons on the gradient meet 4.5:1.
- **Rail (≥ 1280 px, `xl`, v3):** fixed 88 px column. A gradient logo tile (provisional Timely mark) sits at the top-left. A vertical gradient panel holds the navigation icons, is vertically centred (flex, not a fractional translate), sizes to its items, has 24 px right corners and 24 px concave top and bottom fillets that are the same `--curve` as the header, drawn with pseudo-elements (antialiased `border-radius` plus a clipped `box-shadow` ring, no gradient hard stops). Items are 56×47 px with 10 px radius. The active item has a lighter translucent fill plus a visible border and `aria-current="page"`. Names come from tooltips and a screen-reader label. If the list is taller than the viewport the panel scrolls inside its own container.
- **Drawer (< 1280 px):** the existing Radix Dialog drawer, restyled with the same gradient, the full wordmark, labelled items at full-strength white, group titles only when more than one group exists, and **no promotional card**. Closes on navigation. Focus trap and restore from Radix.
- **Content column:** margin after the rail, header above, a centred container `max-w-7xl`, then the footer card (Timely name only, translucent, bordered).
- **Page header:** optional quiet breadcrumb line, H1 (30/36 bold), optional lead text, right-aligned action group (outlined secondary plus one gradient primary).
- **Ambient glow:** one decorative fixed layer behind the content (`aria-hidden`, `pointer-events-none`) made from `glow-1` and `glow-2` radial gradients. Under `prefers-reduced-transparency: reduce` and `forced-colors: active` the glow, blur and gradients are removed and surfaces become solid with a visible border (UI-FR-25).
- **No placeholders (owner decision Q3):** the header has no search, bell or avatar, inert or otherwise. The user area is added by the authentication feature.
- **Not built:** the gear customiser tab, the upgrade card, the diamond button, charts.

### 7.4 Components (UI-FR-16 to UI-FR-19, AC-1.2, AC-8.2, AC-8.4)
Public APIs from v1 are kept where possible. Changes:
- **Card:** translucent surface, 1 px `border`, 24 px radius, padding at the new unit (about 27 px), backdrop blur. `CardHeader` gains an optional `icon` that renders an **IconTile** (44 px, rounded-xl, tinted by tone with token tints).
- **StatCard:** label (uppercase), value (30 bold), hint, trend slot (arrow icon, signed percent, "vs" text, semantic color plus text) and an IconTile (52 px). No product data or charts.
- **ToggleRow:** bordered sub-card with icon tile, title, description and the existing switch.
- **Buttons:** primary uses the gradient (`gradient-start` to `gradient-button-end`) with white text. Secondary is outlined with `border-strong`. Destructive is outlined with `danger`. Large call-to-action (`h-12`, 16 px radius) is a size variant. Pending state and `aria-disabled` behavior from v1 stay.
- **Inputs, textarea, select:** 40 px, 8 px radius, translucent fill, `border-strong`. **Select** is the native element with `appearance-none` and an overlaid chevron icon (owner decision Q6). No custom Radix Select is built.
- **Switch, checkbox, radio:** the existing native-based controls, restyled (blue when on, grey when off, white thumb).
- **Badge, alert, danger card:** tokens only. The danger card variant uses `danger` for border, heading and the destructive action.
- **Tabs, dialog, drawer, dropdown, tooltip, toast, table, pagination, filter bar:** restyled with the same tokens (radius, surface, border, shadow). Their look is **Unverified** against the reference and is not claimed to match. Overlays use opaque `surface-raised`.
- **States:** loading, empty, error and permission-denied use a centred card layout (`StateCard`): icon tile (Tabler icon, our own), optional large status code, heading, text, actions, optional `request_id`. This mirrors the reference's 404 layout without its artwork.
- **Icons:** Tabler through the existing wrapper. Sizes follow the reference's 20 to 24 px, stroke 1.5.

### 7.5 Theme (UI-FR-20, AC-4.1)
Mechanism unchanged: cookie plus inline pre-paint script, no `cookies()` in the layout. The `[data-theme="dark"]` block carries the dark tokens. **Default** is follow-system (owner decision Q4), with the application-level switcher in the header.

### 7.6 Retained boilerplate work
Home page and metadata replacement from v1 stay. `<HealthStatus />` behavior unchanged, inside its `Suspense`. Only its class names are token-based.

**BFF / Route Handlers: None.**

## 8. Tech Choices & Trade-offs
Plan-local decision IDs use the prefix `PD-`.

| # | Decision | Chosen | Status | Why |
|---|---|---|---|---|
| PD-1 | Token mechanism | CSS variables + `@theme inline` | PROPOSED (retained) | Works for the reference's translucent and gradient tokens. One-file brand swap |
| PD-2 | Theme persistence | Cookie + inline script | PROPOSED (retained) | Avoids opting the layout out of prerender |
| PD-3 | Icons | `@tabler/icons-react` | CONFIRMED (v1, owner) | Retained. The reference's icons look like a Lucide-style outline set. Tabler is visually close and already approved |
| PD-4 | Primitives | Radix packages | CONFIRMED (v1, owner) | Retained. Drawer, dialog, menu, tooltip, tabs |
| PD-5 | Toast | In-repo | PROPOSED (retained) | |
| PD-6 | Preview route | Dev-only `ui-preview` | CONFIRMED (v1, owner) | Retained. Extended with the reference-style compositions |
| PD-7 | Test tooling | Option A, no new test dependencies | CONFIRMED (v1, owner) | Retained |
| PD-8 | Mobile table pattern | Scroll container, sticky first column | PROPOSED (retained) | |
| PD-9 | Raw-color guard | Node test | PROPOSED (retained) | Extended to also forbid palette names inside gradient utilities |
| PD-10 | UI rules in `docs/` | `docs/frontend-ui-rules.md` | CONFIRMED (v1, owner) | Retained. Updated for v2 |
| PD-11 | Contrast method | Composite over `canvas` and `glow-peak`, then threshold | PROPOSED (new) | Translucent surfaces cannot be tested as flat colors |
| PD-12 | Rail panel construction | CSS pseudo-elements and radial gradients, no SVG asset | PROPOSED (new) | Avoids copied assets and extra files. Concave joins are approximated, so the owner reviews them (AC-8.4) |
| PD-13 | Spacing unit | `--spacing: 0.28rem` globally | PROPOSED (new) | Matches the observed values. Affects every spacing utility, so v1 components are re-checked |
| PD-14 | Header contents | Sidebar toggle and theme switcher only. No inert placeholders | **CONFIRMED (owner, Q3, 2026-10-11)** | Only functional actions or approved navigation elements. The visual cost (a sparser header) is shown in the review |
| PD-15 | Reference comparison tooling | Ad hoc headless Edge over its DevTools protocol, scripts kept outside the repo | **CONFIRMED (owner, Q7, 2026-10-11)** | No new dependency. It is committed only if repeatable validation later shows a clear need, which would be a new-tooling approval (P7) |
| PD-16 | Palette | **Violet → purple → magenta** (v3), the reference's gradient treatment with Timely-specific values. Replaces the blue-to-teal direction | **CONFIRMED (owner, 2026-10-11)** for the direction and the implemented values | Values are tokens in `globals.css`. Official brand guidelines are DEFERRED |
| PD-17 | Font | **Manrope** (v3). Geist is retired. No Satoshi files, no new dependency | **CONFIRMED (owner, 2026-10-11)** | Same `next/font/google` mechanism. Differences from Satoshi documented |
| PD-21 | Overlays and cursor (v3) | One tooltip style for every tooltip (amber-to-pink pill with arrow, dark text for AA), frosted `glass-menu` dropdowns that size to their items, pointer cursor on interactive controls, disabled placeholders for the account menu | **CONFIRMED (owner, 2026-10-11)** | `--tooltip-start/end/fg` tokens, contrast-tested. Forced-colors and reduced-transparency fallbacks exist |
| PD-22 | Background (v3) | Layered ambient glows (`--glow-1` to `--glow-4`) over a diagonal wash (`--wash-1/2`) in both themes, `--glow-peak` stays the contrast worst case | **CONFIRMED (owner, 2026-10-11)** | The reference background is an image and is not copied. Approximation documented |
| PD-18 | Default theme | Follow system, with a header switcher | **CONFIRMED (owner, Q4, 2026-10-11)** | Retains v1 behavior |
| PD-19 | Sidebar | Desktop icon rail plus responsive drawer, top navbar kept, accessible names and tooltips | **CONFIRMED (owner, Q5, 2026-10-11)** | Matches the observed reference |
| PD-20 | Select | Styled native select | **CONFIRMED (owner, Q6, 2026-10-11)** | No new dependency |

### 8.1 Dependencies (P7)
- **Retained (owner-approved 2026-10-11, installed):** `@tabler/icons-react` 3.49.0, `@radix-ui/react-dialog` 1.2.0, `@radix-ui/react-dropdown-menu` 2.1.25, `@radix-ui/react-tooltip` 1.3.0, `@radix-ui/react-tabs` 1.1.22.
- **New packages: none proposed.**
- **Decisions that would add one:** none. The two alternatives (`@radix-ui/react-select`, a Satoshi font file) were declined by the owner (Q6, Q2).
- **Compatibility checks:** Tailwind v4 features used (`bg-linear-to-r`, `backdrop-blur`, `@utility`, `@theme inline` with alpha tokens) are all supported by the installed version (checked in v1 build). The Radix and Tabler packages already built and ran against React 19.3 and Next 16.4 in v1. `prefers-reduced-transparency` is a newer media query: it is progressive enhancement only, with `forced-colors` as the dependable fallback, and any browser support gap is recorded.

### 8.2 Reassessment of v1 decisions that depended on SmartHR
| v1 decision | Outcome in v2 |
|---|---|
| Slate and blue palette, 4/8/12 px radii, 36 px controls, border-led flat cards | **Replaced** (§7.1, §7.2) |
| 256 px expandable sidebar with collapse toggle | **Replaced** by rail and drawer (Q5) |
| Plain white header with toggle, theme toggle, user placeholder | **Replaced** by the gradient header with toggle and theme switcher only (Q3) |
| No search or notification elements at all | **Retained** (Q3 omits inert placeholders) |
| Type scale 24/32 title | **Replaced** by 30/36 |
| Geist font | **Retained** (Q2) |
| Tabler icons, Radix primitives, preview route, Option A tests | **Retained** |

## 9. Traceability Matrix
| Spec item | Plan section | Notes |
|---|---|---|
| US-1 / AC-1.1, AC-1.2 | §2, §7.1, §7.4, PD-1, PD-9 | Tokens only, guard test |
| US-2 / AC-2.1 to AC-2.3 | §7.3, §4 | Rail, drawer, page header, permission hint |
| US-3 / AC-3.1 to AC-3.3 | §4, §7.4 | State cards, error mapping, toast |
| US-4 / AC-4.1 | §7.1, §7.5, PD-2 | Both themes, pre-paint script |
| US-5 / AC-5.1 to AC-5.7 | §7.1, §7.3, §7.4, §10, PD-11 | Composited contrast, focus, targets, reflow |
| US-6 / AC-6.1 | §7.1, `lib/brand.ts` | Brand swap in two files |
| US-7 / AC-7.1 | §8 PD-10 | Docs updated |
| US-8 / AC-8.1 | §7.3 | Measured shell values |
| AC-8.2, AC-8.3 | §7.2, §7.4 | Shape, spacing, type |
| AC-8.4 | §10, PD-15 | Side-by-side review by the owner |
| AC-8.5 | §7.3 (Not built), §8.1 | No copied assets, no product features |
| UI-FR-1, 2, 9 | §7.1, §7.2, Q1, Q2 | Reference, palette, font |
| UI-FR-11 to 13 | §7.3 | Shell and page structure |
| UI-FR-14, 15 | §7.2 | Shape and density |
| UI-FR-16 to 19 | §7.4 | Inventory including stat card, icon tile, toggle row |
| UI-FR-20 | §7.5, Q4 | Theme |
| UI-FR-21, 22, 24 | §8 PD-10, §7.1 | Ownership, deviations recorded |
| UI-FR-25 | §7.3 | Reduced effects |

## 10. Testing Strategy
Planned only; **nothing in v2 has been executed.** v1 results in `validation.md` apply to the v1 implementation and are superseded.
- **Existing commands:** `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`. The API-client tests and the health-status behavior must stay unchanged.
- **Automated (`node:test`, no new dependencies):**
  - Token completeness for all roles in both themes.
  - **Composited contrast** of every listed pair over `canvas` and `glow-peak` (PD-11), including white on both gradient stops, drawer labels, rail icons, `primary-text`, status colors, `border-strong` and `focus-ring`.
  - Raw-color guard (PD-9), navigation, theme resolver and script, error mapping, status map, pagination, toast logic (retained).
  - Build check: the generated CSS contains the token and gradient utilities and `/` is still a partial prerender.
- **Reference measurement (AC-8.1, AC-8.2, AC-8.3):** in a real browser, read computed styles from the Timely preview and compare with the observed values (header 72 px and 16 px bottom radius, rail 96 px, rail item 56×47 and 10 px radius, container 1280 px, card radius 24 px and padding, control height 40 px and radius 8 px, type sizes), tolerance ±2 px. Method: headless Edge over its DevTools protocol (PD-15). Results go in `validation.md`.
- **Visual comparison (AC-8.4):** side-by-side screenshots of Timely compositions against the reference at 1440, 1024, 768 and 390 px in both themes. **The owner records accept or changes.** Items marked Unverified in the reference are shown without a match claim. Reference screenshots are not committed.
- **Manual accessibility and responsive checks** (AC-5.x): keyboard-only pass, focus not obscured, 24 px targets, 320 px and 400% zoom, reduced motion, reduced transparency and forced-colors, and a screen-reader spot check (rail, drawer, dialog, form, toast). Done by the owner or marked Not executed (P6). The agent never marks these Passed without evidence.
- **Performance check:** note interaction smoothness with blur on in both themes, and compare a build with effects disabled. No numeric budget (D-29).
- Planned and executed results are recorded separately in `validation.md`.

## 11. Risks & Mitigations
- **"Close visual match" versus WCAG 2.2 AA** → the reference fails AA in several places (§7.1, reference-analysis §3). Timely deviates there and lists each deviation. The owner may see visible differences (for example brighter drawer labels, a slightly darker gradient end, stronger input borders).
- **Translucent surfaces make contrast variable** → composited worst-case testing (PD-11), opaque overlays, capped glow, and a solid fallback for reduced transparency and forced colors.
- **Backdrop blur cost on weak devices** → blur only on cards and header, `will-change` avoided, fallback under reduced transparency, measured at validation.
- **Rail panel fidelity (concave joins) and short viewports** → pseudo-element construction is approximate (PD-12). Owner review (AC-8.4). Panel scrolls inside itself when taller than the viewport.
- **Unverified reference states** (dialogs, dropdowns, tables, toasts, hover, focus) → designed from the same tokens, not claimed to match, and flagged in the validation record.
- **Global spacing change (PD-13)** can shift v1 components → visual regression pass on the preview in the tasks.
- **Font difference (Geist vs Satoshi)** → accepted by the owner (Q2), documented in `reference-analysis.md` §7 and shown in the review.
- **Palette mistaken for brand** → names and comments mark it provisional. Brand swap stays a token edit.
- **Reference is a public commercial template** → no code, assets, logos or illustrations are copied (AC-8.5). Measurements and observations only.
- **Inline theme script vs a future CSP** → unchanged (nonce when a CSP is added).
- **Static prerender regressions under `cacheComponents`** → no `cookies()` in the layout, client hooks under `Suspense`, build output checked.
- **Component sprawl** → guard test, ownership rule, review checklist.
- **Manual accessibility evidence is weaker than automated** (Option A) → documented checklist, Option B (Vitest, Testing Library, axe) remains available but is not proposed.
- **v1 `validation.md` becomes stale** → it is marked as covering v1 only. A new validation record is produced after v2 implementation.

## 12. Constitution Check
| Principle | Compliant? | Notes |
|---|---|---|
| P1 Spec first, approval gates | Yes | v2 spec, plan and tasks are `Ready for approval`. Implementation waits for approval and a separate `IMPLEMENT` |
| P2 Decisions labelled | Yes | Owner decisions Q1 to Q7 are recorded as CONFIRMED-on-approval. Exact token values and construction details stay PROPOSED |
| P3 Modular monolith, no speculative layers | Yes | Frontend only. No new layer |
| P4 External systems behind adapters | Yes | None added |
| P5 Security and privacy | Yes | No client authorisation, safe error states, only the `theme` cookie |
| P6 Evidence-based validation | Yes | Planned and executed separated. Manual and visual items are Not executed until run |
| P7 Minimal footprint | Yes | No new dependency proposed. Optional ones are listed and need approval |
| P8 API-first | Yes | No new APIs, no direct data access |

AR-11 to AR-14 (PROPOSED): satisfied (no module dependencies, no internal HTTP, no transactions).

## 13. Decisions and Items for Owner Review
**Decided by the owner on 2026-10-11 (Q1 to Q7)**, recorded in `spec.md` §10 and as PD-14 to PD-20 above: Timely-specific palette, Geist kept, header placeholders omitted, follow-system default, rail and drawer accepted with the top navbar kept, styled native select, comparison tooling outside the repo.

**To confirm at review:**
- **A1 (header):** Q3 is applied to the static avatar too, so the header holds only the sidebar toggle and the theme switcher. See the proposed-layout images.
- **Palette values:** the blue-to-teal values in §7.1 are a proposal inside the confirmed Timely-specific direction.
- **Rail with few items:** today only "Home" exists, so the rail panel will hold a single item until modules are added (the review mockup shows five illustrative items for scale).
- **AA differences:** the table in §7.1 lists what differs visibly from the reference and why.

**Open:** none that blocks approval.

## 14. Change Log
Changes after approval require re-approval (see `docs/sdd-workflow.md` §5).

| Date | Change | Reason | Approved by |
|---|---|---|---|
| 2026-10-11 | v1: initial approval of the plan, with five dependencies, PD-6, PD-7 Option A and PD-10 accepted | Owner approval (`PLAN APPROVED`, `accept recommendations`) | Project owner |
| 2026-10-11 | v2: rebuilt for the OkyAi reference. New token set with composited-contrast method, rail and drawer shell, gradient header, glass cards, new components, reassessed v1 decisions, new decisions PD-11 to PD-15, no new dependencies, open questions Q1 to Q7 | Owner request (`CHANGES REQUESTED`, 2026-10-11) | Pending owner |
| 2026-10-11 | v2 (decisions recorded): Timely-specific blue-to-teal palette replaces the violet values and the AA-difference table was rewritten for it, header placeholders removed, native select and Geist confirmed, follow-system default confirmed, PD-14 and PD-15 confirmed, PD-16 to PD-20 added, §13 rewritten | Owner decisions Q1 to Q7 (2026-10-11) | Pending owner |
| 2026-10-11 | **v3 visual correction, owner-approved after screenshot review:** violet-to-magenta tokens (§7.1 note), header and rail rebuilt (§7.3, 24 px `--curve`, 88 px rail, 144 px offset), account menu placeholder, shared tooltip and menu styles, cursor, footer, layered backgrounds, Manrope. Added PD-21, PD-22. PD-16 and PD-17 replaced | Owner review (2026-10-11) | Project owner |

---
**Status:** Approved · **Approved by:** Project owner · **Date:** 2026-10-11 · **Supersedes:** v1 (approved 2026-10-11)
