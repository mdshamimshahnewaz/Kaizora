# Validation Record — UI Foundation (v2)

> **Purpose:** Prove that each acceptance criterion in `spec.md` v2 is met. A requirement is **Passed** only when it was executed and the result recorded (P6). Planned and executed validation are separate.
> Replaces the v1 record (SmartHR). Date: 2026-10-11. Environment: Windows, PowerShell, Node 24.18.0, Next.js 16.4.0, React 19.3.0, Microsoft Edge (headless, driven over its DevTools protocol; session tools kept outside the repo, Q7).
> **Not executed by the implementing agent:** screen-reader checks, real touch devices, 400% zoom on a real display, and owner acceptance of the visual comparison (AC-8.4).

## 1. Planned Validation
| Spec ID | Planned check |
|---|---|
| AC-1.1, AC-6.1 | `tests/raw-colors.test.mjs`, `tests/tokens.test.mjs` |
| AC-2.x | `tests/navigation.test.mjs`; browser checks of rail, drawer, `aria-current` |
| AC-3.x | `tests/ui-logic.test.mjs`; preview states |
| AC-4.1 | `tests/theme.test.mjs`, `tests/tokens.test.mjs`; browser: theme set at DOMContentLoaded |
| AC-5.1 to 5.7 | Browser measurement and keyboard script; manual checks for screen reader, zoom |
| AC-8.1 to 8.3 | Computed styles read in a real browser vs observed reference values (±2 px) |
| AC-8.4 | Side-by-side screenshots reviewed by the owner |
| AC-8.5 | Code and visual review for copied assets, placeholders, product features |

## 2. Executed Validation
### 2.1 Commands (final code, all run)
| Command | Result | Evidence |
|---|---|---|
| `npm run lint` | Passed | exit 0 |
| `npm run typecheck` | Passed | exit 0 |
| `npm test` | Passed | `tests 46, pass 46, fail 0` (10 API-client tests unchanged and passing) |
| `npm run build` | Passed | Compiled successfully. `/` Partial Prerender (unchanged). `/ui-preview` and `/ui-preview/login` static |
| Production server (`next start`) | Passed | `/` 200. `/ui-preview` and `/ui-preview/login` 404. Served HTML has theme script, skip link, one `<h1>`, `<aside>`, `<header>`, `<footer>`, title "Timely". Built CSS contains `bg-surface`, `rounded-card`, `from-gradient-start`, `text-metric`, `rail-panel`, `ambient-glow`, `glass`, `prefers-reduced-transparency` |
| Dependencies | Unchanged | `package.json` and `package-lock.json` differ from the baseline only by the five v1-approved packages |

### 2.2 Reference measurement, v2 (SUPERSEDED by §2.6 for shell dimensions and font; kept for history)
| Value | Reference (observed) | Timely (measured) | Result |
|---|---|---|---|
| Header height | 72 px | 71.7 px (1440, 1280, 1024, 768, 390, 320) | Passed |
| Header bottom radius | 16 px | 16 px | Passed |
| Header inset | 40 px (md+), 20 px (mobile) by class | 44.8 px and 22.4 px | **Deviation +4.8 / +2.4 px**: the 0.28 rem spacing unit scales `mx-10` and `mx-5`. The reference's own header measured x = 141 px at 1440 (about 45 px from its rail), so this matches its rendered value |
| Header padding / gap | about 27 px / about 18 px | 26.88 px / 17.92 px | Passed |
| Rail width (≥ 1280) | 96 px | 96 px at 1440 and 1280; hidden below 1280 | Passed |
| Rail item | 56×47 px, radius 10 px | 56×47 px, 10 px | Passed |
| Rail panel centring | vertically centred | centre 450 of 450 (1440), 400 of 400 (1280) | Passed |
| Drawer toggle | below the rail breakpoint | visible at 1024, 768, 390, 320; hidden at 1440, 1280 | Passed |
| Content container | 1280 px max | 1280 px at 1440 | Passed |
| Card | radius 24 px, padding 26.88 px, 1 px border | 24 px, 26.88 px, 1 px | Passed |
| Input, select, button | 40 px high, radius 8 px | 40.3 px, 8 px | Passed |
| H1 | 30/36, 700 | 30 px / 36 px, 700 | Passed |
| Card title | 18/28, 600 | 18 px / 28 px, 600 | Passed |
| Metric value | 30/36, 700 | 30 px / 36 px, 700 | Passed |
| Label | about 12 px | 12 px / 16 px | Passed |
| Body | 16/24 | 16 px / 24 px, Geist | Passed (font per Q2) |

### 2.3 Token contrast (AC-5.3, 5.4), `tests/tokens.test.mjs`, composited over the canvas and the worst-case glow peak, both themes
Passed. During implementation the test failed three dark pairs (muted text, primary text and danger text on a card over the brightest glow, 3.7 to 4.05:1). Fixed by lowering dark `surface-muted` to 5% and lightening `fg-muted` (`#a3b1c6`), `primary-text` (`#70b0fc`) and `danger` (`#fb8a8a`). Also checked: text on gradient start and end, rail icons (≥ 3:1), tooltip, focus ring, `border-strong`, `secondary-fg`.

### 2.4 Browser behavior and accessibility (scripted in real Edge, final code)
| Check | Result | Evidence |
|---|---|---|
| Keyboard Tab order (30 stops on `/ui-preview`) | Passed | Starts at the skip link, then logo, rail Home, theme buttons, page actions. Focus never lost |
| Visible focus indicator | Passed | No focused element without a 2 px outline or shadow |
| Focus not obscured (2.4.11) | Passed | The only flagged item is the skip link, which sits above the header by design (fixed, z-70) |
| Drawer (390 px): opens, focus inside, stays inside through 12 Tab/Shift+Tab, Esc closes, focus restored to the toggle, dialog named "Timely navigation" | Passed | Script output |
| Dialog (1440 px): opens, traps focus, Esc closes, focus restored | Passed | Script output |
| Pointer targets ≥ 24 px (home, preview at 1440 and 390, login at 390) | Passed | Only the visually hidden skip link (1×1 until focused) reported. Checkboxes measured 22 px before a fix and were enlarged to 24 px |
| No horizontal page scroll at 1440, 1280, 1024, 768, 390 and 320 px | Passed | `/ui-preview` overflowed at 320 px (grid min-content). Fixed with single-column grids and re-measured: no overflow. `/` and `/ui-preview/login` clean at 1440, 390, 320 |
| Reduced motion | Passed | Transition duration 0.00001 s |
| Reduced transparency | Passed | Blur removed, solid surface `rgb(20, 25, 37)`, glow hidden |
| Forced colors | Passed (emulated) | Blur removed, glow hidden, media query matched |
| Structure on `/`, `/ui-preview`, `/ui-preview/login` | Passed | One `h1`, no heading level skips, `main`, shell landmarks (`header`, `aside`, `footer`), labelled `nav`s, skip link on shell pages, 0 unlabeled form controls, 0 unnamed buttons, `lang="en"` |
| Theme before first paint | Passed | `data-theme="dark"` already set at `DOMContentLoaded` with the cookie set |
| Login Page Preview behavior | Passed | Empty submit sets `aria-invalid` and a linked error message. A valid submit shows "No sign-in was performed. Nothing was sent or stored." **0 network requests**, no cookie, `localStorage` or `sessionStorage` written. The password toggle exposes `aria-pressed` |

### 2.5 Status of the other acceptance criteria
| Spec ID | Result | Notes |
|---|---|---|
| AC-1.1, AC-6.1 | Passed | Guard test passes (including gradient and `white` utilities). All colors in `globals.css`, brand in `lib/brand.ts` |
| AC-1.2, AC-7.1 | Passed (structural) | Preview, home and login are built from shared components. `docs/frontend-ui-rules.md` records ownership and exceptions (PROPOSED) |
| AC-2.1, AC-2.2, AC-2.3 | Passed (script) | Page header, rail with tooltips and screen-reader names, drawer, `aria-current` logic tested. Only Home exists, so nested-group rendering was **not exercised in a browser** |
| AC-3.1, AC-3.2 | Passed (tests) and visually checked in the preview | |
| AC-3.3 | Partly | Live-region structure present (3 regions on `/`). Actual toast announcement by a screen reader **Not executed** |
| AC-4.1 | Passed | Both themes rendered and compared |
| AC-5.1, 5.5, 5.7 (reflow at 320 px) | Passed | Section 2.4. 400% zoom on a real display **Not executed** |
| AC-5.2, 5.4, 5.6 | Passed (scripted) | Section 2.4. Screen-reader output **Not executed** |
| AC-8.1, AC-8.2, AC-8.3 | Passed with one recorded deviation | Section 2.2 |
| AC-8.4 | **Awaiting owner review** | Side-by-side images produced (see the completion report). Not accepted by the owner yet |
| AC-8.5 | Passed | No OkyAi asset, color, source or product feature. No search, bell or avatar. No customiser tab or promo card. The palette test asserts no OkyAi color is used |

## 3. Differences from the reference (visible)
- **Required by WCAG 2.2 AA (plan §7.1):** darker blue-to-teal gradient end, full-white drawer labels, `primary-text` token for links in dark, stronger input borders, opaque overlays, explicit focus ring. Dark `surface-muted`, `fg-muted`, `primary-text` and `danger` were tuned after the composited test.
- **Owner decisions:** Timely-specific palette (Q1), Geist (about 3% to 6% wider than Satoshi, Q2), no header search, bell or avatar (Q3, A1), follow-system default (Q4), native styled select (Q6).
- **Spec requirements the reference lacks:** breadcrumb line above the title.
- **Content:** one rail item (Home) instead of six. No charts, gear tab, promo card or diamond button.
- **Approximate:** the rail's concave joins are drawn with CSS and are close but not identical to the reference.
- **Unverified in the reference, so no match is claimed:** dialogs, dropdowns, tooltips, toasts, tables, hover and focus states.

## 4. API-First Compliance
| Check | Result | Evidence |
|---|---|---|
| Endpoints match the plan | N/A | No endpoints added or changed |
| Frontend uses only the shared API client; no direct Django `fetch` outside `lib/api/` | Passed | `lib/api/client.ts` and its tests untouched. No new `fetch`. The login prototype makes no request (0 network events) |
| No frontend code accesses PostgreSQL or an external system | Passed | |
| Route Handlers / BFF | None | |
| Health-status behavior | Preserved | `health-status.tsx` logic, roles and text unchanged (class names only). Home renders "Django API connected" with the dev backend |

## 5. Constitution Compliance
| Principle | Result | Evidence |
|---|---|---|
| P1 | Compliant | Implementation followed approved spec, plan and tasks v2 and a separate owner instruction |
| P2 | Compliant | New docs PROPOSED. Owner decisions recorded |
| P3 | Compliant | Frontend only |
| P4 | Compliant | No external system. Fonts unchanged |
| P5 | Compliant | No client authorisation. Only the `theme` cookie. The login prototype stores and sends nothing |
| P6 | Compliant | Executed and not-executed items separated above |
| P7 | Compliant | No package or font asset added in v2 |
| P8 | Compliant | No new APIs |

## 6. Outcome
Overall status: **Complete for the automated and scripted scope; owner approved on 2026-10-11.** Open items that remain **Not executed** and are carried as limitations, not passes: screen-reader spot check, real touch devices, 400% zoom on a real display, real-keyboard tooltip focus, and nested navigation groups in a browser (only Home exists). (v3 update: the visual correction in §2.6 was accepted by the owner on 2026-10-11 and T30 is closed; sections 2.2 and 2.4 reflect v2 where they differ from §2.6.) Automated checks and scripted browser checks pass. Still open: (1) your acceptance of the visual comparison (AC-8.4); (2) a screen-reader spot check (shell, drawer, dialog, form, toast) and 400% zoom on a real display, **Not executed**; (3) nested navigation groups have not been rendered because only Home exists.

Known issues and limitations:
1. The Login Page Preview was added at the owner's direction after spec §9 excluded login screens. It is recorded in the spec change log. It has no authentication of any kind.
2. `/ui-preview` and `/ui-preview/login` return 404 in production by design.
3. Header inset is 4.8 px larger than the class-derived 40 px because of the shared spacing unit. It matches the reference's rendered value.
4. `npm install` in the v1 stage reported 5 audit findings that were not investigated.
5. Nothing is committed or staged.

## 2.5 v3 visual correction (owner review, 2026-10-11) — first round
Superseded in detail by §2.6, which re-measured the final code. Dimensions here (96 to 88 px rail, 24 px header corners) are historical.

## 2.6 v3 final verification (final code, 2026-10-11)
Environment: Windows, Node 24.18.0, Next.js 16.4.0 (dev server `http://localhost:3000/`, Django `http://127.0.0.1:8000`), Edge headless over DevTools, system color scheme emulated. Scripts and screenshots stay outside the repo (Q7).

### Commands
| Command | Result | Evidence |
|---|---|---|
| `npm run lint` | Passed | exit 0, no warnings |
| `npm run typecheck` | Passed | exit 0 |
| `npm test` | Passed | `tests 47, pass 47, fail 0` (adds: gradient-mid, tooltip-fg contrast, violet-to-magenta hue range, `--curve`, `--shell-left`, glow-4 and wash roles) |
| `npm run build` | Passed | Compiled successfully. `/` Partial Prerender. `/ui-preview` and `/ui-preview/login` static |
| Dependencies | Unchanged by v3 | No package added. Manrope loads through the existing `next/font/google`. No font files committed |

### Measurements (computed in Edge, AC-8.1 to AC-8.3, v3 values)
| Value | Expected (v3) | Measured | Result |
|---|---|---|---|
| Header | 72 px high, 24 px curve, x 144 at ≥ 1280 | 72 px, 24 px, x 144 (1440 and 1280); x 27 at 1024 and 768; x 13 at 390 and 320 | Passed |
| Rail | 88 px wide at ≥ 1280, hidden below | 88 px at 1440 and 1280, hidden at 1024, 768, 390, 320 | Passed |
| Rail panel | vertically centred, sized to items | y 400, h 101 (centre 450 of 900) | Passed |
| Card / controls | 24 px / 40 px | 24 px card, 40 px input and button (12 px radius, within the 8-12 px brief) | Passed |
| Footer | rounded-top strip at page bottom | y 843 + 57 = 900 | Passed |
| Horizontal overflow | none | none at 1440, 1280, 1024, 768, 390, 320 | Passed |
| Font | Manrope | `Manrope` computed on body, H1 30 px | Passed |
| Cursor | pointer on interactive controls | `pointer` on links and buttons | Passed |

### Behavior (scripted, final code)
| Check | Result |
|---|---|
| Drawer at 390 px: opens, dialog named, focus inside, Esc closes, focus returns to "Open navigation menu" | Passed |
| Theme menu: opens with Enter, focus in menu, 3 items, height 189 px; Esc closes and focus returns to the trigger | Passed |
| Account menu: opens with Enter, 4 items, height 268 px (menu height follows item count); Esc closes and focus returns | Passed |
| Rail tooltip on hover shows "Home" in the shared amber-to-pink style | Passed |
| Rail tooltip on programmatic focus | Not shown. Radix opens tooltips on keyboard focus-visible, which a scripted `focus()` does not trigger. Names remain available through the accessible label. Not executed with a real keyboard |

### Screenshots (actual implementation, `C:\Users\Shamim Shahnewaz\.copilot\session-state\c216845a-a65e-4940-b7ab-ea290894dd4d\files\final\`)
`01-desktop-dark`, `02-desktop-light`, `03-tablet-dark`, `04-tablet-light`, `05-mobile-dark`, `06-mobile-light`, `07-mobile-drawer-dark`, `08-mobile-drawer-light`, `09-profile-menu-dark`, `10-theme-menu-light`, `11-rail-tooltip-dark`, `12-rail-tooltip-light`, `13-preview-dark`, `14-preview-light`. Reviewed by the owner and approved on 2026-10-11 (header and rail curves, backgrounds, menus, tooltips).

### AA-driven and other differences from the reference
- White text on the gradient end is kept at ≥ 4.5:1 (`#c026d3`), a deeper magenta than the reference.
- Tooltip text is dark (`#240a33`) because white on amber fails AA. Light `danger` is `#a81616` for the brighter glow. Dark `primary-text` is a light violet.
- The reference background is an image and is not copied. Layered glows approximate it.
- Satoshi is not added. Manrope is used (owner decision), so glyph shapes and widths differ slightly.
- The account menu is a UI-only placeholder ("Timely user", all entries disabled). There is no search or notification element.
- The reference's page-frame rounded top corners and its other form controls (select, toggle, textarea) were not reproduced or not observable without login. They carry no match claim.
- Only one navigation item exists, so the rail panel is short and nested groups were not rendered in a browser.

### Not executed
Screen-reader testing, real touch devices, 400% zoom on a real display, real-keyboard tooltip focus, and a re-run of the v2 keyboard-order and focus-obscured scripts after v3 (the shell markup gained the account menu and brand link, so the Tab order list in §2.4 is the v2 result).

### 2.7 Final fix after owner approval of the visuals (2026-10-11)
- **Header right-end hairline:** caused by a fractional page margin (53.76 px from the 0.28 rem spacing unit) that put the CSS curve on a half pixel. Fixed by whole-pixel shell margins (14 px, 28 px from sm, 48 px right at ≥ 1280 px). Verified in 3× zoomed screenshots at 1440 px (dark and light) and 390 px (light). Header now spans x 144 to 1392 at 1440 px. The 1024 px close-up was captured but not reviewed.
- Final automated run after this fix: 
pm run lint exit 0, 
pm run typecheck exit 0, 
pm test 47 of 47, 
pm run build compiled, / Partial Prerender, /ui-preview and /ui-preview/login static.
- The §2.6 shell margin values (header x 27 at 1024 and 768, x 13 at 390 and 320) are now x 28 and x 14 respectively. No other measurement changed.

## 7. Change Log
| Date | Change | Reason | Approved by |
|---|---|---|---|
| 2026-10-11 | v2 validation record (replaces v1) | Implementation of spec, plan and tasks v2 | Pending owner |
| 2026-10-11 | v3 verification record (§2.6), T30 accepted by the owner on the final screenshots | Owner review (2026-10-11) | Project owner |
| 2026-10-11 | §2.7 final margin fix. Validation approved by the owner (message `APPROVED ... complete the 001 ui foundation work`, taken as the validation gate because it is the only gate pending) | Owner instruction (2026-10-11) | Project owner |
| 2026-10-13 | Post-closure note: the sidebar rail curve (`.rail-panel::before/::after` in `app/globals.css`) now overlaps the panel by 1px to remove a hairline at fractional display scales (125%, 175%). Found during feature 002 validation; evidence in `specs/002-authentication/validation.md` §1b (E24) and §5. No other 001 behaviour changed | Owner report; reviewed with the 002 validation approval | Project owner, 2026-10-13 |

---
**Status:** Approved · **Approved by:** Project owner · **Date:** 2026-10-11 · **Manual items:** Not executed, listed in §6
