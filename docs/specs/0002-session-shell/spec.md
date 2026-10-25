# 0002: Login, application shell and logout

## Goal and scope
Existing active Django users can sign in to the React app, navigate a responsive
protected shell, and sign out. Use the existing shadcn design system and versioned
DRF API. Existing Admin users work; staff status is not required for app login.

## Acceptance
- A1: Anonymous /app visitors reach /login; protected UI is hidden while checking
  the session. Authenticated /login visitors reach /app. Reload preserves login.
- A2: Username/password login has required-field validation, pending state and
  generic invalid-credential errors (including nonexistent/inactive users).
- A3: Backend enforces CSRF on login AND logout, rotates session/CSRF at login,
  never returns credentials, and sends no-store responses. Login is rate limited.
- A4: App shell includes desktop sidebar, mobile Sheet, Home, account view,
  breadcrumb/title, light/dark/system selector, user menu, accessible logout.
  Future domain modules are labelled unavailable, with no fake metrics or data.
- A4a: Content uses the full available width. A desktop sidebar toggle switches
  between labelled navigation and an icon-only rail; icon links retain accessible
  names and hover labels. Mobile Sheet remains independent.
- A4b: A normal-flow footer sits at the viewport bottom for short content and
  below the content for long pages, appearing only when scrolled to the end.
- A5: Logout invalidates the server session and removes private UI; refresh/back
  cannot restore access. Network logout failures are shown without claiming success.
- A6: Session expiration/other-tab logout is detected on window focus and on a
  periodic check; unavailable backend offers a retry state instead of false logout.
- A7: Existing health/Admin behavior remains; /__ui stays isolated/development-only.

## Boundaries
No signup, password reset/email, social login, MFA, organization membership/RBAC,
business CRUD, native mobile tokens or user database migration. Accounts are
provisioned with Django Admin or createsuperuser. No .env edits or app server startup.

## Evidence
Real PostgreSQL test database: auth lifecycle, CSRF, inactive/bad credentials,
throttle, session revocation, and existing health/Admin regression tests.
Frontend DOM tests: route protection, validation/login, failures, logout/reload state.
Typecheck, lint, schema generation and production build; browser on user-run server
if available. Record any unavailable verification explicitly.
