# Timely V4 — Frontend UI Rules

> **Status:** PROPOSED. Added by `specs/001-ui-foundation` (plan PD-10, v2; updated for the owner-approved v3 visual correction, 2026-10-11). Not CONFIRMED until the owner confirms it.
> **Purpose:** Keep every feature page consistent by binding it to the shared UI foundation (spec UI-FR-21, UI-FR-22, UI-FR-24, AC-7.1).
> Server/API rules stay in `docs/frontend-api-client.md`. Next.js rules stay in `frontend/AGENTS.md`.

## 1. Look and feel
- The visual language follows the OkyAi dashboard as a **reference only**: a gradient header and icon rail, translucent bordered cards (24 px radius), 40 px controls (8 px radius), a 72 px header and an 88 px rail (v3). Nothing is copied from it. Timely uses **its own violet-to-magenta palette** (v3, replacing the blue-to-teal palette), its own icons and its own brand.
- The palette and `frontend/lib/brand.ts` are **provisional**, not brand approval. A brand change edits `globals.css` and `lib/brand.ts` only.
- **Manrope** is the font (owner decision 2026-10-11; the closest free match to the reference's Satoshi, which is not added). Do not add font files or font packages without approval. Type sizes use the named tokens (`text-title`, `text-heading`, `text-lead`, `text-body`, `text-caption`, `text-metric`).

- The page background is layered ambient glows (`--glow-1` to `--glow-4`) over a diagonal wash (`--wash-1/2`) in both themes. The reference background is an image and is not copied.
- Form controls follow the reference's Content Tools inputs: 40 px high, 8-12 px radius, faint border, optional leading icon (`Input icon=`). Other control types are not verified against the reference.

## 2. Tokens only
- All colors, radii, shadows, spacing and type sizes come from the tokens in `frontend/app/globals.css` (utilities such as `bg-surface`, `text-fg-muted`, `border-border`, `rounded-card`, `from-gradient-start to-gradient-end`).
- No hex values, `rgb()/hsl()` literals, Tailwind palette utilities (`bg-zinc-50`), `white`/`black` utilities or arbitrary color values in `app/` or `components/`. `frontend/tests/raw-colors.test.mjs` enforces this.
- Both themes must work: use semantic tokens, never `dark:` color overrides.
- Translucent surfaces (`glass`) must stay legible over the ambient glow. `frontend/tests/tokens.test.mjs` checks every foreground/background pair over the worst-case backdrop. Add a pair there when you add a new foreground token.

## 3. Accessibility deviations from the reference
- Where the reference's value fails WCAG 2.2 AA, use the nearest passing token and **do not copy the reference value** (spec UI-FR-24). Known cases: white text on the reference's gradient end, faint navigation labels, primary used as dark-theme text, 12% input borders, grey focus ring, translucent overlays. Overlays use the opaque `surface-raised`.
- The tooltip text is dark (`--tooltip-fg`) because white on the amber end fails 4.5:1. The light-theme `danger` token is darkened for the brighter glow.
- Effects are decorative. Blur, gradients and the glow degrade to solid surfaces under `prefers-reduced-transparency` and `forced-colors`.

## 4. Shared components
- Shared components live in `frontend/components/ui/` (primitives, states) and `frontend/components/shell/` (shell, rail, drawer, page header, breadcrumbs). Icons are imported only in `components/ui/icon.tsx`.
- Features **compose** these components and do not fork or copy them. If something in the inventory exists, use it (AC-1.2).
- Every page renders inside the shell and starts with `PageHeader` (one H1, optional breadcrumbs, one primary action).
- Cards: `Card` with `CardHeader` (optional icon tile). Metrics: `StatCard`. Settings rows: `ToggleRow`. Dangerous areas: `Card variant="danger"`.
- Every data region defines loading, empty and error states (`LoadingState`, `EmptyState`, `ErrorState`). Map API failures with `describeError` and never render raw error text.
- Status is shown with `Badge` and its single status map (text and icon, never color alone).
- Server-side pagination only, using `Pagination` with the `{count,next,previous,results}` envelope.
- `Select` is the styled native element. A custom select needs owner approval (new dependency).

## 5. Shell and navigation contract
- At 1280 px and wider the shell shows an 88 px icon rail (content offset 144 px via `--shell-left`). Below that it shows a labelled off-canvas drawer opened from the header. The header is a 72 px gradient bar with 24 px curves (`--curve`, shared with the rail) holding the drawer toggle, the brand name, the round theme menu and the round account menu. The account menu shows the signed-in user's name and email and a working Log out (spec 002); Profile, Settings and Help stay disabled until the features that own those pages exist. The sign-in page (`/login`) renders without the shell. Do not add search, notification or other user elements until the feature that makes them functional exists.
- Every tooltip uses the shared `Tooltip` (amber-to-pink pill with an arrow, dark text for AA). Dropdown menus use the shared frosted `DropdownMenuContent` and size to their items. Do not style tooltips or menus per feature.
- Interactive controls show the pointer cursor (global rule in `globals.css`). Disabled controls show not-allowed. Do not override cursors per component.
- The footer is a rounded-top strip at the bottom of the page.
- Add a feature's destinations as a `NavGroup` in `frontend/lib/navigation.ts`. Never hardcode items in pages, the rail or the drawer. Every item needs a label (it becomes the accessible name and the tooltip).
- `permission` is a display hint that hides entries. The server enforces access (P5).
- `validateNavigation` (tested) requires unique ids, valid internal hrefs and at most two levels.

## 6. Promotion and exceptions
- A new shared component, or a one-off that departs from these rules (own colors, spacing, button style, navigation pattern), needs a recorded justification and **owner approval before merge** (AC-7.1). Record it in the feature's `plan.md`.
- A component starts inside its feature. It moves to `components/ui/` only after owner approval.

## 7. Theme
- Light, dark and follow-system (default), switched from the header. The preference is a non-sensitive `theme` cookie, applied before first paint by an inline script. The root layout must not read `cookies()` (it would opt the app out of static prerendering).
- If a Content-Security-Policy is added later, the inline script needs a nonce (plan §5).

## 8. Accessibility baseline (WCAG 2.2 AA)
- Controls have visible labels, errors are tied with `aria-describedby`, icon-only buttons need a `label`, targets are at least 24×24 px, focus is never hidden by sticky regions, and motion respects `prefers-reduced-motion`.
- Overlays use the Radix-based wrappers. Do not reimplement focus trapping, menus or tooltips.

## 9. Preview routes
- `/ui-preview` (App Shell and every component) and `/ui-preview/login` (a **visual prototype only**: no authentication, session, storage or API call) exist for review. They return 404 in production and appear in no navigation.
