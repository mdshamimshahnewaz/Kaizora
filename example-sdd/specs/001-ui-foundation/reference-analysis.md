# Reference Analysis — UI Foundation (v2: OkyAi)

> **Supports:** `specs/001-ui-foundation/spec.md` (v2). **Primary reference:** https://okyai.mantrakshdevs.com/dashboard (inspected 2026-10-11). It replaces SmartHR, which is no longer a reference.
> The reference is a visual and UX reference only. No source code, assets, logos, illustrations or branding are copied, and no product-specific AI features are adopted.
> Reference screenshots are kept **outside the repository** (session workspace) because they contain third-party imagery. This document records measurements and observations instead.

## 1. Evidence and limitations
**Inspected (2026-10-11):**
- **Rendered pages in a real browser** (headless Microsoft Edge driven through its DevTools protocol, no packages installed): `/dashboard` at 1440×900 (dark and light), 1280×800 (light), 1024×768, 768×1024, 1920×1080 and mobile 390×844 (light, with the navigation drawer open); full-page captures of `/settings`, `/subscription`, `/analytics`; `/error` (404) and `/login`.
- **Computed styles** read from the live DOM at 1440 px (header, sidebar, main, H1, card, card title, input, navigation buttons).
- **The shipped CSS** (`index-7NqR_VEh.css`): `:root` and `.dark` token blocks.
- **The shipped JavaScript bundle** (read only to identify routes, layout class names, breakpoints, the default theme and the fact that the demo login performs no real authentication). It is not copied.

**Not inspected:** dropdown menus, dialogs, tooltips, toasts, tables (none were found on the pages visited), focus rings, hover/pressed states, the settings customiser panel, the notification bell panel (clicking it showed no panel), the user control (it navigated to `/login`), the chatbot and content-tools pages beyond one screenshot each, the expanded desktop sidebar (if one exists), keyboard behavior, screen-reader output, and any state requiring real data.

**Terms used below**
- **Observed:** seen in a rendered screenshot or read from computed styles or shipped tokens.
- **Inferred:** deduced from observed values or class names (for example a breakpoint), not confirmed in a rendered state.
- **Unverified:** not seen. Timely's treatment is a proposal.

## 2. Observed design characteristics

### 2.1 Layout and shell
| Characteristic | Value | Status |
|---|---|---|
| Overall composition | Slim vertical sidebar on the left, a floating gradient header bar across the top of the content, content column below | Observed |
| Header | Sticky, height 72 px (`h-16` at the reference's spacing unit), background gradient left→right from the primary violet to magenta, **only the bottom corners rounded (16 px)**, horizontal inset 20 px (mobile) and 40 px (≥ md) from the content edges, inner padding about 27 px, item gap about 18 px | Observed (computed) |
| Header contents (left→right) | Sidebar toggle (below the rail breakpoint only), search field (448×40 px, translucent white fill, 8 px radius, leading icon), then right-aligned: theme toggle icon, notification bell with a small red dot, circular user avatar button | Observed |
| Sidebar (≥ 1280 px) | Fixed **icon rail**, 96 px wide, no labels. The logo sits on top of the page background. Navigation icons sit in a **vertical gradient panel** (violet at the top to magenta at the bottom, with concave curved cut-outs where it meets the page) that is **vertically centred** in the viewport and about 400 px tall. Each item is a 56×47 px button with 10 px radius. The active item has a lighter translucent fill and border. Inactive icons are translucent white | Observed |
| Sidebar (< 1280 px) | The rail disappears. A toggle button appears in the header. It opens an **off-canvas drawer with labels**: the full logo on top, the same gradient background, a vertical item list (icon and label), and a promotional "Upgrade" card at the bottom | Observed (1024, 768, 390 px). Breakpoint of 1280 px inferred from the class names (`xl`) and confirmed between the 1024 and 1280 captures |
| Desktop collapse/expand control | None seen at ≥ 1280 px. The rail is the only desktop state | Observed (absence). A hover-expand behavior is **unverified** |
| Content container | `max-w-7xl` (1280 px), centred, full width within the column | Observed (class names and layout) |
| Footer | A bordered translucent card at the end of the page with copyright text left and credit text right | Observed |
| Floating extras | A violet tab on the right edge with a gear icon (theme customiser) and a circular diamond button at the bottom-left (upgrade) | Observed. **Not adopted** (see §4) |
| Background | Dark: near-black violet with faint violet glows. Light: white with soft lilac and grey blurred glows | Observed |

### 2.2 Page structure
| Characteristic | Value | Status |
|---|---|---|
| Page header | H1 at 30/36 px, weight 700; a muted subtitle below it; actions right-aligned on the same row (one outlined button with an icon, one gradient primary button with an icon). No breadcrumb was seen on any visited page | Observed |
| Section rhythm | Cards separated by about 27 px; metric cards in a 4-column grid at 1440 and 1024 px, 2 columns at 768 px; larger cards in 2-column splits (about 2/3 and 1/3 on `/settings`) | Observed |
| Metric (KPI) card | Small uppercase label, large bold value (30 px), muted sub-line, a trend row (arrow icon, green or red percentage, "vs last month"), and a rounded-square **icon tile** in the top-right | Observed |
| Settings-style card | Card header with a rounded **icon tile** (tinted per meaning: violet, green, blue), title (18/28, weight 600) and a muted description; form body; row-style toggle items inside bordered sub-cards | Observed |
| Danger zone | A card with a red tinted border and fill and red heading text, holding a destructive outlined action | Observed |

### 2.3 Shape, spacing and type (computed at 1440 px)
| Token | Value | Status |
|---|---|---|
| Spacing unit | `--spacing: 0.28rem` (4.48 px) instead of Tailwind's 0.25rem. Everything on the Tailwind scale is about 12% larger | Observed (shipped CSS and computed values) |
| Card | Radius 24 px, 1 px border, padding 26.88 px, internal gap 17.92 px, shadow `0 1px 3px` (very light) | Observed (computed) |
| Controls | Radius 8 px. Input height 40 px, 1 px border, translucent fill, shadow `0 1px 2px`. Buttons 14/20 px, weight 500, icon gap 9 px | Observed (computed) |
| Large call-to-action buttons | `h-12`, radius 16 px, gradient fill with a coloured shadow | Inferred (class names; seen on a promotional card) |
| Navigation item | Radius 10 px (`--radius: 0.625rem`) | Observed |
| Header | Bottom radius 16 px | Observed |
| Body type | 16 px / 24 px base. Card title 18/28 weight 600. H1 30/36 weight 700. Small labels about 12–13 px, uppercase with letter spacing | Observed |
| Font | **Satoshi** (a third-party font file). Fallback `sans-serif` | Observed |
| Icons | Outline icons with rounded strokes, about 20–24 px, in the Lucide style | Observed (visual style, icon set not confirmed) |

### 2.4 Color tokens (shipped `.dark` block, converted to sRGB for reference)
| Role | Dark value | Notes |
|---|---|---|
| `background` | `#070712` (oklch 13.6% .025 283) | Near-black violet |
| `foreground` | near-white (oklch 98.4%) | |
| `card` / `popover` / `input` | white at 6% opacity | Translucent surface over the glow background |
| `border` | white at 12% opacity | About 1.4:1 against the card and background (blended as a browser does). Decorative |
| `primary` | `#7a4aff` (oklch 58% .26 287) | Violet |
| `sidebar-primary` (gradient end) | `#c425e4` (oklch 60.8% .27 320) | Magenta |
| `muted-foreground` | `#90a1b9` | |
| `destructive` | `#ff6467` | |
| `chart-2` (success green) | `#00bc7d` | |
| `ring` | grey (oklch 55.1%) | Focus ring is a neutral grey, not violet |
| Light theme | `background` white, `card` white at 40% opacity, same primary. Light text and secondary colors were not extracted in full | Observed (partial) |

Default theme on first load is **dark** (the app reads a `theme` value from local storage and defaults to `dark`). Text direction can be switched (RTL support exists). Both are Observed in the bundle. They are not Observed in a rendered state for RTL.

### 2.5 Components seen
Buttons (gradient primary, outlined secondary, outlined destructive), text input, custom select with chevron, toggle switch (on/off), avatar circle with initials, badge-style labels ("MOST POPULAR"), progress bars, icon tiles, circular check bullets, translucent cards, a bordered footer card. A 404 page shows an illustration, a large violet "404", a heading, text and two buttons (outlined "Go Back" and violet "Go Home") in a centred translucent card.

## 3. Observations that matter for accessibility (the reference does not meet WCAG 2.2 AA everywhere)
Ratios below were computed from the converted token values (WCAG 2 formula). Items marked "estimate" involve alpha blending and are approximate.

| Observation | Ratio | Consequence for Timely |
|---|---|---|
| White text on the primary `#7a4aff` | 4.95:1 | Passes for normal text |
| White text on the gradient end `#c425e4` | 4.44:1 | **Fails** 4.5:1. Timely must darken the gradient end or avoid text there |
| Inactive navigation items (about 60% white on the gradient) | about 3.0–3.2:1 (estimate) | Acceptable for icon-only rail items only if icons are at least 3:1 (borderline). **Fails** for text labels in the drawer. Timely uses full-strength white for drawer labels |
| Primary `#7a4aff` used as text or a link on the dark background | 4.05:1 | **Fails** for normal text. Timely needs a lighter primary text token |
| `border` (white 12%) and the input border (same value) | about 1.4:1 against the card | Fine for decorative card edges. **Fails** the 3:1 target for input boundaries (WCAG 1.4.11). Timely uses a stronger `border-strong` for form controls |
| `foreground` on dark `background` | 19.1:1 | Passes |
| `muted-foreground` on dark `background` | 7.6:1 | Passes |
| Destructive and success colors on dark | 6.9:1 and 8.1:1 | Pass |
| Light theme muted text (black at about 50%) | not reliably computed here | To be verified when light tokens are defined |
| Focus ring (grey, oklch 55%) | not measured in a rendered state | **Unverified** |

Timely's tokens will deviate from the reference wherever these fail. Each deviation is listed in the plan and shown in the validation record.

## 4. Mapping: observed OkyAi pattern → proposed Timely treatment
| OkyAi pattern | Status | Timely treatment |
|---|---|---|
| Slim vertical rail with a centred gradient navigation panel, concave curves | Observed | **Adopt** as the desktop (≥ 1280 px) sidebar, drawn with Tailwind and an inline-SVG or CSS shape that is our own. Keep one nested level and tooltips for names (rail has no labels). Active item uses `aria-current="page"` plus the translucent fill |
| Off-canvas labelled drawer below 1280 px, opened from a header toggle | Observed | **Adopt** (Radix Dialog drawer already present) |
| Logo above the rail, full logo in the drawer | Observed | **Adopt the arrangement** with Timely's provisional mark and wordmark from `lib/brand.ts`. No OkyAi logo or asset |
| Gradient header with bottom-rounded corners, inset from the edges, sticky | Observed | **Adopt** |
| Header search field | Observed | **Not adopted** (owner decision Q3). No search, functional or inert |
| Header theme toggle (single icon) | Observed | **Adopt** the position. Timely keeps three choices (light, dark, system) in one compact control |
| Header notification bell with red dot | Observed | **Not adopted** (owner decision Q3) |
| Header user avatar | Observed | **Not adopted** (Q3, interpretation A1). It returns with the authentication feature |
| Page header: 30/36 bold title, muted subtitle, right-aligned actions | Observed | **Adopt.** Breadcrumbs stay (required by the approved spec) as a quiet line above the title. This is a deliberate addition the reference does not show |
| Footer card | Observed | **Adopt** with Timely's name only (no credit text) |
| Translucent "glass" cards, 24 px radius, 1 px border, 27 px padding | Observed | **Adopt** as the card token set. Surfaces are composited and contrast-checked, not assumed |
| Metric (KPI) card with icon tile and trend row | Observed | **Adopt the pattern** as a reusable `StatCard` shell (label, value, hint, trend slot, icon tile). No product metrics, no charts |
| Card header with icon tile, title, description | Observed | **Adopt** (icon-tile card header) |
| Toggle rows (icon, title, description, switch) | Observed | **Adopt** as a list-row pattern built on the existing switch |
| Gradient primary button, outlined secondary button, outlined destructive button | Observed | **Adopt** |
| Inputs: 40 px, 8 px radius, translucent fill, 1 px border | Observed | **Adopt.** The border is strengthened where needed for 3:1 |
| Custom select | Observed | **Styled native select** (owner decision Q6). No new dependency |
| Danger-zone card (red tint) | Observed | **Adopt** as an alert/card variant |
| 404 / error card with illustration and two buttons | Observed | **Adopt the layout** for the standard error and access-denied states. No mascot illustration or copied artwork. Timely uses its own icon |
| Ambient glow background (dark violet glows, light lilac glows) | Observed | **Adopt** as a decorative, non-interactive background layer built from tokens (`aria-hidden`), with a reduced-effects fallback |
| Violet → magenta palette | Observed | **Adopted as a direction (owner correction, 2026-10-11, supersedes Q1).** Timely uses its own violet → purple → magenta values, not OkyAi's exact hex colors. The earlier blue-to-teal palette was dropped as too far from the reference |
| Satoshi font | Observed | **Not adopted** (owner decision Q2). Geist is kept. Differences are listed in §7 |
| Dark theme by default | Observed | **Not adopted** (owner decision Q4). Timely follows the system theme, with a header switcher |
| Right-edge gear tab (theme customiser) | Observed | **Do not adopt** (spec §9 excludes the customiser) |
| Upgrade/pro promotion card and diamond button | Observed | **Do not adopt** (product-specific) |
| Charts, AI metrics, chatbot, content tools, pricing and the demo login | Observed | **Do not adopt** (product-specific or out of scope) |
| RTL support | Observed (bundle) | **Out of scope** (spec: DEFERRED) |
| Tables, dialogs, dropdowns, tooltips, toasts, focus and hover states | **Unverified** | Timely designs these with the same tokens (radius, translucent surface, border, shadow). They are **not claimed to match** the reference |

## 5. Not adopted, explicitly
OkyAi logos and images, the robot and mascot artwork, the "Upgrade" promotional content, AI/chatbot/analytics/content/subscription features, the credit line, the Satoshi font files, **the violet and magenta colors**, the header search, notification and avatar elements, and any source code. Timely uses its own violet-to-magenta palette (owner correction, 2026-10-11).

## 6. Owner decisions applied (2026-10-11)
Q1 Timely-specific palette with the reference's gradient treatment. Q2 Geist kept. Q3 no inert search, notification or user elements. Q4 follow-system default with a theme switcher. Q5 desktop rail and responsive drawer accepted, top navbar kept, accessible names and tooltips. Q6 styled native select. Q7 comparison tooling outside the repo. Recorded in `spec.md` §10.

> **v3 update (owner decision 2026-10-11):** the font is now **Manrope**, not Geist (Q2 superseded). The reference computed styles (dashboard, 1440 px): body Satoshi 16/400, H1 30/700, weights 300, 400, 500, 700, 900 loaded. Satoshi is not added. The Geist comparison below is kept for history; Manrope is also somewhat wider than Satoshi, with the same expected effects (earlier wrapping, wider metrics), and shapes differ.

## 7. Typography: Geist versus the reference font (Q2, superseded)
The reference uses Satoshi. Timely keeps Geist. **Measured** on 2026-10-11 with canvas text measurement in headless Edge, at the same sizes and weights (Satoshi from the live reference, Geist from the Geist Latin subset the app already ships):

| Text (size, weight) | Satoshi | Geist | Geist relative width |
|---|---|---|---|
| "Dashboard" (30 px, 700) | 152.9 px | 159.6 px | +4.4% |
| "12,543" (30 px, 700) | 92.8 px | 98.5 px | +6.1% |
| "Usage Trends" (18 px, 600) | 113.6 px | 116.9 px | +2.9% |
| "Monthly requests, tokens, and revenue" (14 px, 400) | 235.0 px | 245.6 px | +4.5% |
| "View Reports" (14 px, 500) | 83.5 px | 87.1 px | +4.3% |
| A 46-character sentence (16 px, 400) | 340.1 px | 351.2 px | +3.3% |

Geist is about 3% to 6% wider at equal sizes. Expected effects, to be checked in the side-by-side review (AC-8.4): slightly longer lines, earlier wrapping of long labels, and slightly wider metric values. Glyph shapes also differ (visible in the review images), which is a stylistic difference and is not measured here. Type sizes, weights and line heights follow the reference values.

## 7a. v3 observations (2026-10-11, dashboard and Content Tools, computed styles)
- Body background is an image (saas-bg) on a near-black violet base (`oklch(0.136 0.025 283)`). Not copied. Timely approximates it with layered glows.
- Input: 40 px, 8 px radius, 1 px border at 12-20% white, fill 5-6% white, 14 px text, leading search icon (40-45 px left padding). Round 40 px icon buttons in the header. Cursor is `pointer` on buttons.
- Not observable without login: other form controls (select, toggle, textarea).

## 8. Change Log
| Date | Change | Reason | Approved by |
|---|---|---|---|
| 2026-10-11 | v1 (SmartHR), approved together with the spec v1 | Owner approval (`SPEC APPROVED`) | Project owner |
| 2026-10-11 | v2: replaced SmartHR with OkyAi, added rendered and computed evidence, observed/inferred/unverified split, accessibility findings and the mapping | Owner request (`CHANGES REQUESTED`) | Pending owner |
| 2026-10-11 | v2 (decisions recorded): mapping rows updated for owner decisions Q1 to Q6, added §6 and the measured typography comparison in §7 | Owner decisions (2026-10-11) | Pending owner |
| 2026-10-11 | v3: palette direction adopted (violet to magenta), font changed to Manrope, dashboard and Content Tools computed styles recorded (§7a) | Owner review (2026-10-11) | Project owner |
