# Verification — 2026-10-17

## Implementation
A1–A7 implemented: session API, username/password login, protected responsive shell,
read-only account view, theme menu, logout, session reconciliation and failure states.
Existing Django users are used. No database model/migration or .env changes.
No development servers were started or stopped during this feature task.

## Automated evidence
- New backend lifecycle test failed first with 404 before endpoints existed.
- Backend final: 14 tests passed on the repository Docker PostgreSQL's isolated
  test database, with an environment override; user's configured DB untouched.
- Covers active/non-staff login, bad/inactive/missing users, CSRF on anonymous
  login and logout, session/CSRF rotation, old-cookie revocation, throttling,
  deactivation, JSON auth CSRF errors and unchanged Admin error pages.
- Frontend initial test collection failed before app implementation existed.
  After implementation and correcting the matchMedia test stub: 7 tests passed.
- Frontend tests cover loading/anonymous guards, login return route, required-field
  validation, credential rejection, restoration, logout failure/success, focus expiry,
  and unavailable-session retry. They mock the API boundary, not the app components.
- TypeScript, ESLint, Ruff lint/format, Django system check: passed.
- Three module boundary tests plus boundary scan: passed.
- OpenAPI validation/export and generated TypeScript: passed.
- Migration dry-run: no changes detected. The sandbox could not query the user's
  configured database for migration-history validation; real auth DB tests used
  isolated PostgreSQL instead.
- Production build: passed. Route splitting removed the initial >500kB warning;
  main JS approximately 383kB / 123kB gzip, with login/shell/pages split separately.
- Latest dependency installation audit: zero vulnerabilities.

## Browser evidence
Used the user's already-running frontend/backend. No server started by the agent.
- Separate unauthenticated browser: desktop login rendering; 390px mobile layout
  and required-field validation; no horizontal overflow.
- Existing signed-in browser: real authenticated home and account details rendered;
  390px mobile Sheet opens, account navigation closes it, no horizontal overflow.
- Restored viewport and original /app route after checking. No logout of the user's
  existing session was performed. End-to-end credential submission/logout was
  covered by isolated backend tests plus frontend behavior tests, not by entering
  the user's credentials in the browser.
- Existing app preview console: no errors observed during final inspection.

## Review
Simplification reviews: reuse and quality no findings; efficiency fix prevents
unchanged session polls from rerendering consumers; one redundant comment removed.
Test-value review retained both proof suites. Revision and mutation race guards,
CSRF handling, accessibility labels and required security checks preserved.

Code review: skipped (ce-code-review unavailable) — its scope stage requires a Git
base; this workspace is not an initialized Git repository, so it cannot produce a
scoped receipt. No native local-diff reviewer was available (only PR CI tooling).
Manual final file review covered authentication, CSRF/error serialization, route
protection, logout failures, redirect restrictions, stale reads and provider cleanup.
No blocking issue remained. No Git commit, push or PR was attempted.

## Dependencies and operational limits
Added react-router 7 (MIT), compatible with existing React 19 and Node engine;
Vitest, jsdom and Testing Library are development-only test dependencies. Existing
npm lockfile retained and updated. Official router guidance is linked in design.md.
The login throttle uses local-memory cache; production requires shared cache and
proxy-aware rate limiting. HTTPS/same-origin deployment and cookie policy remain
required. Organization authorization, signup/reset/MFA and native mobile tokens
are explicitly outside this increment. Future module entries are disabled and
marked Soon; no business data is fabricated.

## Full-width and collapsible sidebar follow-up
- Removed the shell's centered max-width and account card width cap.
- Desktop toggle switches 240px sidebar to 72px icon rail; accessible names and
  native hover labels retained. Mobile Sheet uses independent expanded navigation.
- Browser measured 1869px viewport: expanded 240px + 1629px content; collapsed
  72px + 1797px content. Both toggle directions verified.
- Frontend typecheck, lint, existing 7 tests and production build passed.

## Normal-flow footer follow-up
Added a flex-column/minimum-viewport-height app body, growing main content and a
non-fixed footer. Browser: footer bottom equals viewport bottom at 911px with short
content; at 390×600 its top is 1067px, below the visible screen. Typecheck, lint and
production build passed. No new tests for this layout-only change.


## User-guide follow-up — 2026-10-18

Owner requested configuration/examples and mandatory guide delivery. The [user guide](../../user-guide/README.md) now covers this feature in `login`. [Guide verification](../../user-guide/verification.md) records content/interaction/build checks and the unverified browser visual pass. This follow-up does not change prior implementation evidence or imply owner acceptance.
