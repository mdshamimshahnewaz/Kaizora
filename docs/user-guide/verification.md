# User-guide delivery verification

Date: 2026-10-18. Scope: current 0001–0008 workflows, operator configuration,
browser-readable documentation, footer entry point and mandatory future guide updates.
Authority: explicit owner request for an example-based complete guide and guide completion
with every subsequent feature. No new business workflow, DB write or server startup.

## Executed checks

- Cross-checked organization/role usage, permission catalog, UI form labels, project
  transitions/immutable fields, resource link/team date rules, Admin model labels,
  backend environment loading and Vite proxy against current source.
- Confirmed backend reads DATABASE_URL only; guide does not pretend separate DB_*
  values work. Examples contain placeholder credentials, not live secrets.
- JSDOM check passed: 16 chapters, unique IDs, valid fragment links, matching search,
  no-results filtering, anchor reset, print button wiring and exact Vite build copy.
- Frontend ESLint passed. Production build passed, including TypeScript checking.
- Existing app footer now links /user-guide/; static public content ships under
  dist/user-guide/index.html. No new dependency or external asset is used.
- P10, root AGENTS.md, SDD workflow/tasks/verification templates and each implemented
  feature verification record carry the guide completion requirement or coverage link.

## Limits

Browser tool request to open the guide timed out during automatic approval review;
no visual/browser inspection is claimed. Responsive/print styles exist and DOM
interactions were checked, but narrow-screen rendering and actual printed PDF were
not visually verified. Documentation examples were checked against code; this turn
did not execute sample business mutations or rerun unchanged backend tests. Owner
readability/UX acceptance remains pending. No commit, publication or production rollout.

## Routing correction — 2026-10-18

User reported Page not found at /user-guide/. Live HTTP reproduction confirmed that
Vite returned the React app HTML for the directory URL while the explicit
/user-guide/index.html returned the guide. Added a narrow directory-index rewrite
before Vite's SPA fallback in both development and preview middleware.

Live existing development server now returns HTTP 200 with the actual guide title
for /user-guide/, /user-guide, /user-guide/?from=footer and /user-guide/index.html.
/app and /user-guide-missing still return the usual SPA entry. ESLint and production
build (including TypeScript) passed. No server was started by the agent. Preview
hook is configured but no preview server was started or independently exercised.
This HTTP verification closes the previously unchecked directory URL; it does not
claim visual browser/print verification. Production hosts still need directory index
serving before SPA fallback as documented in the guide index.

## Settings refresh guidance — 2026-10-18

Guide #roles now explains the one-minute/focus background access checks. The Settings
fix retains the current view during background requests; explicit manual/conflict
retry and failed access checks still clear the prior snapshot. Two failing-before,
passing-after interaction regressions cover focus and timer refresh without remounting
Settings. Full frontend suite: 48 passed; tenant isolation/revocation cases retained.


## Resource selection refactor — 2026-10-18

Guide People/Teams/Workforce/Admin/walkthrough updated for direct searchable member selection, name-only no-login resources, and separate project workforce/access. Existing manual duplicate-person setup removed from the walkthrough. Feature evidence: [0009](../specs/0009-resource-selection/verification.md). No claim that TL/PM task/time entry exists.
