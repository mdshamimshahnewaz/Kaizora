# Feature Spec — Authentication (Microsoft Entra ID SSO)

> **Purpose:** WHAT is being built and WHY, with no technical solution. Technical decisions are in `plan.md`.
> **Location:** `specs/002-authentication/spec.md`. **Rules:** `docs/constitution.md` (P2, P4, P5, P8), `docs/architecture.md`.
> **Process note:** at the owner's instruction (2026-10-11) the spec, plan and tasks were prepared in one pass and written as files marked `Ready for approval`, instead of drafting the spec in the conversation first (`docs/sdd-workflow.md` §1 rule 3). Nothing here is approved. Each document needs its own approval phrase.
> Every decision is marked CONFIRMED, PROPOSED, OPEN or DEFERRED. Nothing in this document is CONFIRMED yet.

## 1. Summary
Timely V4 has no authentication. Every API endpoint is open, including one that exposes server details, and the frontend shows a placeholder account menu. This feature lets employees sign in with their organisation's Microsoft Entra ID account (single sign-on), lands them in the App Shell, protects every page and API operation by default, gives the system a trustworthy identity and a role for each user, manages the sign-in session, and lets users sign out. It is the security foundation that every later feature depends on. It does not decide what any role may do in later features.

## 2. User Stories
- **US-1 (P0):** As an employee, I want to sign in with my Microsoft work account, so that I do not need a separate password for Timely.
- **US-2 (P0):** As a signed-in user, I want to arrive in the App Shell (to the page I originally asked for, if any), so that I can start working immediately.
- **US-3 (P0):** As the organisation, I want every page and every API operation to refuse unauthenticated visitors by default, so that employee data is not exposed.
- **US-4 (P0):** As the organisation, I want each signed-in person to be recognised as one stable Timely user with roles assigned and controlled inside Timely, so that access is decided by Timely and not by what the sign-in token claims.
- **US-5 (P0):** As a signed-in user, I want my session to last for a sensible time and then end safely, so that an unattended device does not stay signed in forever.
- **US-6 (P0):** As a signed-in user, I want to sign out, so that nobody else can use my session on a shared device.
- **US-7 (P1):** As a user whose sign-in fails or who is not allowed in, I want a clear, safe message and a way to retry, so that I know what to do without learning internal details.
- **US-8 (P1):** As a security owner, I want sign-in, sign-out and refusal events recorded, so that they can be reviewed (P5).

## 3. Acceptance Criteria

### US-1 — Sign in with Microsoft
- **AC-1.1:** Given I am not signed in, when I open the sign-in page, then I see the Timely sign-in screen (matching the approved login preview's look) with one "Sign in with Microsoft" action and no email or password fields.
- **AC-1.2:** Given I choose "Sign in with Microsoft", when I complete Microsoft's sign-in, then I return to Timely signed in as myself.
- **AC-1.3:** Given I sign in from a browser that already has a Microsoft session, then I am still shown an account choice, so that a shared device does not silently reuse the previous person's account.
- **AC-1.4:** Given a sign-in attempt was not started from Timely, or was started in another browser, or is reused or has expired, when it returns to Timely, then it is refused and no session is created.
- **AC-1.5:** Given an account from a Microsoft tenant other than the organisation's, when it signs in, then it is refused.
- **AC-1.6 (amendment A-1, PROPOSED):** Given the organisation's Entra redirect URI is `<application origin>/api/auth/callback/azure-ad`, when Microsoft returns me to that address after sign-in, then Timely processes the response and completes or refuses the sign-in as in AC-1.2/1.4 (it is never sent to the sign-in page first), and the redirect address is taken from configuration, not duplicated in code.

### US-2 — Arrive in the App Shell
- **AC-2.1:** Given I have just signed in with no earlier destination, then I land on the App Shell home page.
- **AC-2.2:** Given I was sent to sign in while asking for an internal page, when I finish signing in, then I land on that page.
- **AC-2.3:** Given the requested destination is external, malformed or not an internal path, then I land on the home page instead (no open redirect).
- **AC-2.4:** Given I am signed in, when I open the sign-in page, then I am taken to the App Shell instead.
- **AC-2.5:** Given I am signed in, then the App Shell account menu shows my name and email (or equivalent display identity), and the sidebar shows only entries my roles permit. The hiding is a convenience only (AC-3.4).

### US-3 — Protected pages and API
- **AC-3.1:** Given I am not signed in, when I open any application page other than the sign-in page and the sign-in callback, then I am sent to the sign-in page and, after signing in, returned to that page (AC-2.2).
- **AC-3.2:** Given I am not signed in, when any API operation other than the explicit public exceptions is called, then it is refused as unauthenticated.
- **AC-3.3:** Given I am signed in but my role does not permit an operation, when I attempt it, then it is refused as forbidden by the server, regardless of what the page showed or what the token claimed.
- **AC-3.4:** Given I change the page, request or token claims on my own device, then my access does not change (P5).
- **AC-3.5:** The explicit public exceptions are limited to: the health check, the sign-in start, the sign-in completion, and the sign-in page and callback pages. The server-diagnostics operation is no longer public (see §4).
- **AC-3.6:** Given a user's Timely account is deactivated, when they make their next request, then it is refused, even if their session has not expired.

### US-4 — Identity and role mapping
- **AC-4.1:** Given I sign in, then Timely recognises me by my stable Microsoft identity (tenant and user identifier), not by my email address or name, so that a changed or reused email cannot give me someone else's account.
- **AC-4.2:** Given I sign in for the first time, then a Timely user is created for me **with no roles** (PROPOSED, see OQ-2), and I can sign in and see my own identity but nothing else.
- **AC-4.3:** Given I sign in again, then I am matched to the same Timely user and my display name and email are refreshed from Microsoft.
- **AC-4.4:** Given roles are assigned or removed in Timely, then my access changes on my next request (not only at next sign-in).
- **AC-4.5:** Given the sign-in token carries group or role claims, then they are ignored for access decisions in this feature (PROPOSED, see OQ-3).
- **AC-4.6:** Given a signed-in user, then they can read their own identity and role names (to display and to hide unavailable navigation), and no one's identity through this feature other than their own.
- **AC-4.7:** An authorised operator can assign and remove a role for a user through a controlled operator procedure, because no user-management screen exists yet (PROPOSED, see OQ-3).

### US-5 — Session
- **AC-5.1:** Given I am signed in, then my session ends after a period of inactivity (PROPOSED 30 minutes) and after a maximum lifetime regardless of activity (PROPOSED 8 hours), then I must sign in again.
- **AC-5.2:** Given my session has ended, when I use the app, then I am sent to sign in with a "session ended" message and returned to my page afterwards.
- **AC-5.3:** The session credential is not readable by page scripts and is never stored in browser storage; it is not sent to other sites (P5).
- **AC-5.4:** Microsoft tokens are not kept after sign-in completes and never reach the browser (PROPOSED; see §5).
- **AC-5.5:** Given a session is ended on the server, then it cannot be used again even if the credential was copied.

### US-6 — Logout
- **AC-6.1:** Given I choose "Log out" in the account menu, then my Timely session is ended on the server, the browser credential is removed, and I see the sign-in page with a "signed out" message.
- **AC-6.2:** Given I have logged out, when I use the browser's back button or the old credential, then protected pages and API operations are refused.
- **AC-6.3:** Given a logout request is not made by my own browser from Timely's pages (cross-site request), then it is refused.
- **AC-6.4:** Logout ends the Timely session only; it does not sign me out of Microsoft (PROPOSED, see OQ-5). The account choice at the next sign-in (AC-1.3) covers shared devices.

### US-7 — Failure states
- **AC-7.1:** Given Microsoft is unavailable or returns an error, when I try to sign in, then I see a retryable "sign-in is unavailable" message.
- **AC-7.2:** Given I cancel at Microsoft or my account is refused, then I see a clear "sign-in was not completed" message and can retry.
- **AC-7.3:** Given my Timely account is deactivated, then I see a "no access" message with who to contact (contact text OPEN, see OQ-8).
- **AC-7.4:** Messages never reveal tokens, tenant settings, internal identifiers, stack traces or whether a particular account exists.
- **AC-7.5:** If the backend is unreachable, protected pages show the shared "unavailable" state; they never show protected content or fail open.

### US-8 — Audit
- **AC-8.1:** Given any of these happens: sign-in started, sign-in succeeded, sign-in refused (with a reason category), user first created, logout, session ended by timeout, access refused for a deactivated user, role assigned or removed, then a record is stored with time, user (if known), event type and request identifier.
- **AC-8.2:** Audit records contain no tokens, codes, secrets or session credentials.

## 4. Operations Clients Need

| Operation | Who may perform it | Related AC |
|---|---|---|
| Start a Microsoft sign-in | Anyone (public, necessarily) | AC-1.x |
| Complete a Microsoft sign-in | Anyone with a valid, unexpired, matching attempt (public, necessarily) | AC-1.x, AC-4.x |
| Read my own identity, role names and session expiry | Any signed-in user | AC-2.5, AC-4.6 |
| End my session | Any signed-in user | AC-6.x |
| Assign or remove a user's role (operator procedure) | Operator with server access (not a screen; OPEN who, OQ-3) | AC-4.7 |
| Read server diagnostics (existing operation) | Restricted to superusers (PROPOSED, OQ-6); was public | AC-3.5 |
| Health check (existing operation) | Anyone (explicit exception, unchanged) | AC-3.5 |

## 5. Data and Ownership (business level)
- **Owner:** a new Accounts area (users, role assignments, sign-in attempts, audit events) owned by the backend (module name proposed in `plan.md`; module list is OPEN D-22).
- **Data:** a Timely user keyed by Microsoft identity (tenant, user id), display name, email, active flag, last sign-in time; role assignments; short-lived sign-in attempts; sessions; audit events.
- **Sensitivity:** personal data (name, email) and security-relevant data. Microsoft tokens are not stored (PROPOSED). No Microsoft secrets in code, logs, responses or docs; configuration from the environment (P5).
- **Retention:** sign-in attempts expire within minutes. Audit retention is DEFERRED (D-30). Session retention follows the session lifetime.
- **Not decided here:** role names and what each role may do in later features (OPEN OQ-3).

## 6. External Systems and Dependencies
- **Microsoft Entra ID:** used to prove who the person is (sign-in, account choice, tenant). Accessed only by the backend through an adapter (P4); the browser is merely redirected to Microsoft's sign-in page. Microsoft Graph is **not** used in this feature.
- **Dependencies:** App Shell and login preview from `specs/001-ui-foundation` (closed; reused, not reopened). Needs the organisation's app registration details from the owner (OQ-1).
- **Resolves:** `docs/decisions.md` D-21 (authentication mechanism), D-20 (browser-to-Django path, as it relates to sessions), and the keep-or-remove decision of D-18 for installed auth packages, once the owner approves.

## 7. Non-Functional Requirements
- **Performance:** sign-in completes within a few seconds under normal Microsoft latency; the per-request session check adds negligible delay. Numeric targets OPEN (D-29).
- **Security:** P5 in full. Server-side deny-by-default. Replay, tampering, cross-site and open-redirect attacks on the sign-in and logout flows are refused (AC-1.4, AC-2.3, AC-6.3). Identity is never matched by email. Secrets only from the environment.
- **Auditability:** AC-8.x. Audit events and revocation targets are PROPOSED here for owner confirmation (D-30).
- **Accessibility/i18n:** sign-in and message screens meet the AA expectations of `docs/frontend-ui-rules.md`, are keyboard-operable and announce errors; English only.

## 8. Edge Cases & Error States
- Returning from Microsoft with an error, cancel, missing or repeated parameters, expired attempt, or cookie blocked.
- User opens two tabs or double-clicks "Sign in".
- Account in another tenant, guest/external accounts, or a personal Microsoft account.
- Email changed in Microsoft since last sign-in (identity must still match, AC-4.1); two Microsoft users with the same email.
- Deactivated user with a live session (AC-3.6).
- Session expires while a page is open; API returns unauthenticated → sign-in with return path.
- Clock skew between servers and Microsoft token times.
- Backend or Microsoft down (AC-7.1, AC-7.5).
- Browser back after logout (AC-6.2).
- Role removed while the user is active (AC-4.4).
- Unreachable or misconfigured Microsoft settings: sign-in fails safely with a generic message and the configuration error is logged without secrets.

## 9. Out of Scope
- User-management, role-management or admin screens; self-service profile; password, MFA or account recovery (handled by Microsoft).
- Local username/password sign-in, "remember me", social or non-Microsoft sign-in.
- Entra group/app-role synchronisation, Microsoft Graph calls, provisioning/deprovisioning from Entra, and automatic sign-out when Microsoft disables an account (DEFERRED, see R-3 in `plan.md`).
- Business permissions of later features (attendance, employees, reports) and role names beyond the mechanism (OQ-3).
- Mobile/native clients, API tokens for non-browser clients, SSO between other apps, rate limiting, CORS/CSRF policy beyond this feature (D-40).
- Changing the Django admin site's own login; changing the module structure beyond what the plan proposes; the old `/ui-preview/login` prototype stays as is.
- Any AI or ML.

## 10. Open Questions
Only decisions that change security outcomes are listed. Each has a recommendation. All must be resolved or DEFERRED before the plan is approved.

| ID | Question | Options | Recommendation |
|---|---|---|---|
| OQ-1 | **Organisation's Entra app registration** (tenant ID, client ID, redirect URI, client secret) and tenant model | Single-tenant (only this organisation) / multi-tenant | Single-tenant, enforced by the backend. The owner supplies the non-secret IDs via the backend environment; secrets are never shared in chat or files. Register the redirect URI of the Next.js origin. **Amended (A-1, 2026-10-13):** the owner's existing registration is `http://localhost:3000/api/auth/callback/azure-ad` in development and **cannot be changed**; the application adapts to it (plan §14). |
| OQ-2 | **Who may sign in and how users are created** | (a) any user of the tenant is created on first sign-in with **no roles**; (b) only pre-registered users; (c) auto-create with a default role | (a), plus "Assignment required" on the Entra enterprise app so only assigned people can reach Timely at all. (b) cannot work until a user-management feature exists; (c) would invent a role. |
| OQ-3 | **Role model and vocabulary** | (a) Roles stored and assigned in Timely (Django groups); token claims ignored. (b) Roles taken from Entra groups/app roles in the token. | (a), which follows P5 ("not by token claims alone"). Initial role names and what they permit are **not** set here; later features define them. Assignment through an operator command until a user-management feature exists. Entra group mapping DEFERRED. Who the operators are: owner to confirm. |
| OQ-4 | **Browser-to-Django path and session carrier** (D-20, D-21) | (a) Browser talks only to Next.js; Next.js Route Handlers (BFF) relay sign-in and logout and hold an HttpOnly session cookie; Django owns session validity. (b) Browser calls Django directly with cookies. | (a), as already recommended in D-20; needs a BFF register entry (`docs/architecture.md` §3). |
| OQ-5 | **Session lifetime and logout scope** | Idle/absolute timeout values; Timely-only logout vs also sign out of Microsoft | Idle 30 min, absolute 8 h; Timely-only logout with account choice on each sign-in (AC-1.3, AC-6.4). |
| OQ-6 | **Foundation security fixes tightly coupled to sessions** (D-27) | (a) Include in this feature: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` from the environment; diagnostics restricted to superusers. (b) Leave for a separate spec. | (a). Session signing and cookies are only as safe as the secret key, and leaving diagnostics public contradicts AC-3.2. Needs owner approval because D-27 says they need their own spec. |
| OQ-7 | **Dependencies** (P7, D-18) | Use the already-installed `requests`, `PyJWT`, `cryptography` (no new installs). Do not use `django-allauth`, `djangorestframework_simplejwt`, `oauthlib`. | Approve the three for use; remove the three unused auth packages from `backend/requirements.txt` as a task (the owner may instead defer removal). |
| OQ-8 | **Contact text for the "no access" message** | A support address or team name | Owner to supply, or the message says "contact your administrator". |

**Resolution (2026-10-11):** the owner accepted the recommendation for OQ-1 to OQ-8. OQ-8 contact text: "contact your administrator" until the owner supplies one. The owner-side items of OQ-1 (app registration and `.env` values) remain task T0.

Defaulted, not blocking (PROPOSED unless the owner objects): audit retention DEFERRED (no purge in this feature); the audit event list in AC-8.1; Entra tokens are discarded after sign-in and no refresh token is requested, meaning a person disabled in Microsoft keeps access until their Timely session ends (at most 8 hours) or is deactivated in Timely.

## 11. Change Log
| Date | Change | Reason | Approved by |
|---|---|---|---|
| 2026-10-13 | **Amendment A-1:** OQ-1 now names the owner's existing redirect URI `<origin>/api/auth/callback/azure-ad`; new AC-1.6. Rest of the spec unchanged. | Owner cannot change the Entra registration; the application must match it | Project owner, 2026-10-13 |
| 2026-10-13 | Feature closed with the validation approval. No spec change. AC-1.6 Passed (`validation.md`); limitations in `validation.md` §6. | Owner validation approval | Project owner, 2026-10-13 |

---
**Status:** Approved · **Feature closed:** 2026-10-13 · **Approved by:** Project owner · **Date:** 2026-10-13 (incl. amendment A-1) · **Linked constitution:** `docs/constitution.md` (v1.1)
