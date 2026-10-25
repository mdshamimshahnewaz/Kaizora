# Technical Plan — Authentication (Microsoft Entra ID SSO)

> **Purpose:** HOW `specs/002-authentication/spec.md` will be implemented. Every decision traces to a spec item.
> **Rules:** `docs/constitution.md`, `docs/architecture.md`, `docs/api-conventions.md`, `docs/frontend-api-client.md`.
> Every decision is PROPOSED until the owner approves. The plan depends on the spec's OPEN questions OQ-1 to OQ-8; each dependency is flagged where it applies (assuming the spec's recommendations).
> **Approved by the owner 2026-10-11 (amendment A-1 2026-10-13); feature closed 2026-10-13.** Originally written at the owner's request in the same pass as the spec (see the spec's process note). If the spec changes, this plan is re-checked.

## 1. Linked Spec
Source: `specs/002-authentication/spec.md` · Covers: US-1 to US-8.

## 2. Architecture Overview
Django owns authentication: it runs the OpenID Connect sign-in with Entra, validates the identity, creates the user, and owns the session. Next.js only presents the pages and relays three browser navigations (sign-in start, callback, logout) so the browser never talks to Django (D-20 / OQ-4) and the session credential lives in an HttpOnly cookie on the Next.js origin.

```
Browser ──GET /auth/login──▶ Next BFF ──POST login/start/──▶ Django (accounts)
   ◀── 302 to Entra (state, nonce, PKCE challenge; prompt=select_account) ◀── + sets timely_login cookie (binding)
Browser ──▶ Entra (user signs in) ──302 /auth/callback?code&state──▶ Next BFF
Next BFF ──POST login/complete/ {code,state,binding}──▶ Django ──token request (code + secret + PKCE verifier)──▶ Entra
   Django validates the ID token, maps identity → user, creates session, audits
Next BFF ◀── {session_key, session_expires_at, next} ── sets timely_session cookie (HttpOnly), 302 to safe next
Every later page/API call: Next server ──Authorization: Session <key>──▶ Django (authenticates on every request)
```

- **Backend module `accounts` (PROPOSED; module list is OPEN D-22).** Owns identity, role assignment, sign-in attempts, audit events, session authentication and the Entra adapter. Depends on: Django `auth`/`sessions` (framework only). No dependency on `core`. `core` depends on `accounts` (one direction, AR-11): it uses `accounts.permissions` for the diagnostics endpoint.
  - `accounts/models.py`, `services.py` (use cases, the module's public interface), `authentication.py` (DRF class), `permissions.py`, `adapters/entra.py`, `api/` (views, serializers, urls), `management/commands/assign_role.py`, `tests/`.
- **Frontend:** `app/login/`, `app/auth/{login,callback,logout}/route.ts`, `proxy.ts`, `lib/auth/`, `lib/api/accounts.ts`; `AppShell`, `ProfileMenu` and `app/page.tsx` get small changes. No business logic in Next.js (AR-1).
- **Transaction boundary (AR-13):** `complete_login` is one atomic transaction owned by `accounts` (consume attempt, create or update user and identity, create session, write audit).

## 3. Data Model and Ownership
```
Entity: EntraIdentity            Owner module: accounts
  user: OneToOne(auth.User)       — the Timely user (framework model kept; no AUTH_USER_MODEL swap)
  tenant_id: UUID, object_id: UUID — unique together; the identity key (AC-4.1). Email is never a key.
  created_at, last_sign_in_at
Entity: LoginAttempt             Owner module: accounts   (short-lived, single-use)
  state_hash (sha256, unique), binding_hash (sha256), nonce, code_verifier,
  next_path, created_at, expires_at (10 min), consumed_at
Entity: AuthEvent                Owner module: accounts   (append-only audit)
  occurred_at, event_type, user (FK, null on delete SET_NULL), reason (category), request_id
Roles: django.contrib.auth Group (+ Django permissions). Role = Group; assignment = group membership. (OQ-3)
Sessions: django.contrib.sessions (database). Extra keys: auth_time (for absolute lifetime).
```
- Other modules read identity/roles only through `accounts` public functions and DRF permission classes, never its models (AR-5, AR-8). Cross-module foreign keys: none introduced (D-31).
- Passwords: users are created with an unusable password. Django's default `User.username` is set to a generated value (`entra-<object_id>`); email and names are display data.
- Migrations: one initial `accounts` migration. The existing foundation (`core`) has no models.
- Expired `LoginAttempt` rows are deleted opportunistically at each sign-in start. No scheduler (D-40).

## 4. API Contract
Base: `/api/v1/accounts/` (PROPOSED D-12). All responses use the PROPOSED error envelope (D-11, §5). Session-bearing responses send `Cache-Control: no-store`. Authentication on every authenticated endpoint is `Authorization: Session <key>`; the DRF default authentication class is `accounts.authentication.SessionHeaderAuthentication` and the default permission is `IsAuthenticated` (deny by default).

```
POST /api/v1/accounts/auth/login/start/
  Purpose:        Begin an Entra sign-in (US-1, AC-1.1–1.4, AC-1.3)
  Auth:           Public. Justification: the user is not signed in yet.
  Permission:     AllowAny. Only the Next.js server is expected to call it; no CORS is enabled.
  Request:        { next?: string }  — internal path only (see §5), max 512 chars; invalid → treated as "/"
  Response 200:   { authorization_url: string, binding: string }
                    authorization_url is built only from the configured Entra authority; it carries state, nonce,
                    PKCE S256 challenge, scope "openid profile email", prompt=select_account, response_mode=query.
                    binding is a random secret shown once; only its hash is stored.
  Errors:         503 auth_unavailable (Entra settings missing/invalid or discovery unreachable; generic detail)
```
```
POST /api/v1/accounts/auth/login/complete/
  Purpose:        Finish the sign-in and create the session (US-1, US-2, US-4, AC-1.2, 1.4, 1.5, 4.x, 7.x)
  Auth:           Public. Justification: the caller has no session yet; protection is state + binding + PKCE + single use.
  Permission:     AllowAny
  Request:        { code?: string, state: string, binding: string, idp_error?: string(≤64) }
                  Either code or idp_error is required.
  Response 200:   { session_key, session_expires_at, next, user: <Me> }
  Errors:         400 invalid_attempt  — unknown, expired, reused, wrong-binding or malformed attempt (one uniform error)
                  400 sign_in_not_completed — idp_error supplied (user cancelled or Entra refused); attempt consumed
                  403 account_not_permitted — tenant (tid) mismatch or missing oid
                  403 account_inactive — Timely user deactivated (AC-7.3)
                  502 idp_unavailable — token request or key fetch failed (retryable)
  Sequence:       lock attempt (select_for_update) → verify not expired/consumed and binding hash (constant-time)
                  → mark consumed → token request with PKCE verifier → validate ID token (§6) → get_or_create identity
                  → refresh display name/email → check is_active → create session (auth_time) → audit.
```
```
GET /api/v1/accounts/me/
  Purpose:        Current identity for the App Shell and the navigation display hint (AC-2.5, AC-4.6)
  Auth:           Authenticated
  Permission:     IsAuthenticated; returns only the caller's own data (no object ids in the URL)
  Response 200:   <Me> = { display_name, email, roles: string[], permissions: string[], is_superuser: bool, session_expires_at }
                  roles = group names; permissions = "app_label.codename" values. Both may be empty (AC-4.2).
  Errors:         401 not_authenticated | session_expired | account_inactive (the last two use code to let the UI choose a message)
```
```
POST /api/v1/accounts/auth/logout/
  Purpose:        End the server-side session (US-6, AC-6.1, 6.2, 5.5)
  Auth:           Authenticated
  Permission:     IsAuthenticated
  Response 204:   (no body) session flushed, audit written
  Errors:         401 (already ended; the BFF treats it as success)
```
Existing endpoints changed (AC-3.2, AC-3.5, OQ-6):
- `GET /api/health/` — explicitly `AllowAny` with no authentication classes. Behaviour unchanged.
- `GET /api/system-info/` — now `IsAuthenticated` plus `accounts.permissions.IsSuperuser` (PROPOSED, OQ-6). Behaviour otherwise unchanged. This is an approved-requirement change of existing behaviour (spec AC-3.5).

Internal interface of `accounts` (in-process, AR-12): `services.start_login`, `complete_login`, `end_session`, `me_payload`, `assign_role`, `remove_role`; `permissions.IsSuperuser`, `permissions.HasRole(*names)` (for later features); `authentication.SessionHeaderAuthentication`.

Pagination, filtering, sorting: none (no list endpoints).

## 5. Security
- **Authentication per request:** `SessionHeaderAuthentication` reads `Authorization: Session <key>`, loads the Django session, rejects it if missing/expired, checks absolute lifetime (`auth_time` + 8 h, else flush and 401 `session_expired`), loads the user, rejects inactive users (AC-3.6, 401 `account_inactive`), and slides the idle expiry (30 min). Because the user and roles are read on each request, role removal and deactivation apply immediately (AC-4.4, AC-3.6).
- **CSRF:** the browser never sends a Django-readable cookie to Django; the credential travels in a custom `Authorization` header set only by the Next.js server, which cross-site pages cannot add. Django's cookie-based CSRF is therefore not relied on for these endpoints. State-changing browser requests to Next.js (logout) are protected by `SameSite=Lax` plus an explicit Origin/Sec-Fetch-Site check (AC-6.3). CORS stays off (D-40: no wider policy decided).
- **Sign-in flow protections:** authorization code flow with PKCE (S256), server-held `state` and `nonce`, single-use attempt with 10-minute expiry, and a browser binding (random secret in a short-lived HttpOnly `timely_login` cookie, `Path=/auth/callback`, `SameSite=Lax`, compared to the stored hash) so an attempt started in one browser cannot be completed in another (AC-1.4, login CSRF/fixation). Replay and tampering return the single uniform `invalid_attempt`.
- **Token validation (§6):** signature via the tenant JWKS, `iss`, `aud`, `exp`/`nbf`/`iat` with 60 s leeway, `nonce`, `tid` equal to the configured tenant (AC-1.5), `oid` required, algorithm pinned to RS256. Identity = `(tid, oid)`; email and name are display only (AC-4.1). Group/role claims are not read (AC-4.5). The client secret is sent only in the back-channel token request.
- **Open redirect (AC-2.3):** `next` must be a relative path starting with a single `/`, no `//`, `\`, scheme, control characters or whitespace, ≤ 512 chars, and not `/login` or `/auth/*`; otherwise `/`. Validated in Django at start and again in the BFF before redirecting. The same pure function is unit-tested in both languages.
- **Session credential:** cookie `timely_session`, HttpOnly, `SameSite=Lax`, `Secure` outside development, `Path=/`, `Max-Age` = remaining absolute lifetime. Never in browser storage and never exposed to client components (AC-5.3). Logging never includes the cookie, key, code, tokens or secret.
- **Microsoft tokens:** access, ID and refresh tokens are discarded after validation; `offline_access` is not requested (AC-5.4).
- **Deny by default:** DRF default permission `IsAuthenticated`; the public list is exactly: health, login start, login complete (AC-3.5). A test enumerates every URL pattern and fails if a public endpoint is not on that list.
- **Frontend gate:** `proxy.ts` is an optimistic redirect only (cookie present or not). The authoritative check is `requireUser()` in each page's server code, which calls `/me/`; Django enforces access on every data call (AC-3.1, AC-3.3). The UI never decides access; the navigation `permission` hint only hides entries.
- **Foundation hardening (OQ-6):** `SECRET_KEY`, `DEBUG` (default `False`), `ALLOWED_HOSTS` from the environment; the hardcoded key is removed from source. The owner must set `SECRET_KEY` in their local `backend/.env` (I will not read or edit `.env`). A new, strong key invalidates nothing important (no sessions exist).
- **Error envelope (D-11, PROPOSED):** one exception handler returns `{type,title,status,code,detail,errors[],request_id}`; `request_id` is taken from `X-Request-ID` or generated; no stack traces or internals (P5).
- **Audit (AC-8.x, D-30 PROPOSED):** events `login_started`, `login_succeeded`, `login_refused` (reason category: `invalid_attempt`, `idp_error`, `tenant_mismatch`, `inactive`), `user_created`, `logout`, `session_expired`, `access_refused_inactive`, `role_assigned`, `role_removed`. No tokens, codes, secrets, session keys, IP addresses or user agents. Retention DEFERRED. Audit write failure on sign-in fails the sign-in closed (no session without an audit record).
- **Rate limiting** is DEFERRED (D-40); see R-5.

## 6. External Systems and Adapters
- **Adapter:** `accounts/adapters/entra.py`, port: `build_authorization_url(state, nonce, code_challenge) -> str`, `exchange_and_validate(code, code_verifier, nonce) -> VerifiedIdentity(tenant_id, object_id, email, display_name)`. Vendor claims never leave the adapter (P4).
- **Direction:** outbound HTTPS to `login.microsoftonline.com` only (OIDC discovery for the single tenant, JWKS, token endpoint). Read-only identity; no Graph.
- **Libraries:** already-installed `requests` (timeouts 5 s, no redirects, TLS verify on), `PyJWT` + `cryptography` (RS256). Discovery and JWKS cached in memory for 1 hour; an unknown `kid` triggers one refresh (OQ-7; P7 approval needed).
- **Failure behaviour:** network/timeout/5xx → `EntraUnavailable` → 502 `idp_unavailable`; invalid token/tenant mismatch → `EntraRejected` → 403/400; missing configuration → 503 `auth_unavailable` and a secret-free log line. Never fail open.
- **Configuration (environment only):** backend `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_TENANT` (tenant ID), `MICROSOFT_REDIRECT_URI` (already named in `backend/.env.example`), plus `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `AUTH_SESSION_IDLE_SECONDS` (1800), `AUTH_SESSION_ABSOLUTE_SECONDS` (28800). Frontend (server-only): `API_URL` (existing) and `APP_ORIGIN` (non-secret; used for the Origin check and secure-cookie decision). No secret reaches the frontend or `NEXT_PUBLIC_*`.
- **Owner actions outside the code (OQ-1):** register the app, set the redirect URI to `<APP_ORIGIN>/auth/callback`, create the secret, set "Assignment required", and place the values in `backend/.env`.

## 7. Frontend
Read `frontend/node_modules/next/dist/docs/` (`authentication.md`, `proxy.md`, `cookies.md`, route handler docs) before writing Next code.

- **Pages/components**
  - `app/login/page.tsx` (server): reads `next`, `notice`/`error` search params, redirects signed-in users (AC-2.4), renders `LoginCard`: brand, "Sign in with Microsoft" link to `/auth/login?next=…`, themed like the approved preview (reuse `components/ui`, `BrandMark`, `Alert`); messages for `signed_out`, `session_ended`, `unavailable`, `not_completed`, `no_access` (AC-5.2, 6.1, 7.x). Add `/login` to `BARE_ROUTES` so it renders without the shell.
  - Root layout resolves the current user (only when the cookie exists) and passes it to `AppShell`/`ProfileMenu`: name, email, and a "Log out" form (`POST /auth/logout`). Navigation `isAllowed` uses `roles`/`permissions`/`is_superuser` as a display hint only.
  - `app/page.tsx` and every future page call `requireUser()` first (§5).
  - The old `/ui-preview/login` prototype is left unchanged.
- **Shared client (`lib/api/`):** refactor `client.ts` into a reusable `apiRequest` that keeps today's rules (server-only, `API_URL` validation, 5 s timeout, `redirect: "error"`, `no-store`) and adds method/JSON body, forwarding `Authorization: Session`, and mapping error envelopes into `ApiClientError` (`status`, `code`, `errors[]`, `request_id`) per `docs/frontend-api-client.md` §4. `getHealth` keeps its signature and tests. `lib/api/accounts.ts` provides `startLogin`, `completeLogin`, `getMe`, `logout`.
- **Error and empty states:** 401 → sign-in with `next`; 403 → shared forbidden state; network/timeout/5xx → shared "unavailable" state (AC-7.5). Protected content is never rendered on failure.
- **BFF / Route Handlers (justified, register in `docs/architecture.md` §3):**

| Handler | Why Django alone is not enough | Does | Must not |
|---|---|---|---|
| `GET /auth/login` | The browser must be redirected, and a binding cookie set on the Next.js origin | Calls `login/start/`, sets `timely_login`, 302 to Entra | Contact Entra, hold secrets, decide access |
| `GET /auth/callback` | Entra redirects the browser to the Next.js origin; the HttpOnly session cookie is set here (P5 allows cookie handling in a BFF) | Reads `code`/`state`/`error` and `timely_login`, calls `login/complete/`, sets `timely_session`, clears `timely_login`, 302 to a validated `next` or to `/login?error=…` | Validate tokens, create users, trust query parameters beyond forwarding them |
| `POST /auth/logout` | The cookie lives on the Next.js origin | Origin check, calls `logout/`, clears cookie, 303 to `/login?notice=signed_out` | Decide access |

  `proxy.ts` (optimistic cookie-presence redirect; matcher excludes `_next`, static files, `/login`, `/auth/*`) is not a handler and is not a security boundary.

## 8. Tech Choices & Trade-offs
| Decision | Options considered | Chosen | Status | Why |
|---|---|---|---|---|
| Who runs OIDC | Next.js (e.g. Auth.js) / Django | Django adapter; Next.js relays | PROPOSED (OQ-4) | P4/P8: Entra only via backend adapters; no new frontend dependency |
| Session mechanism | JWT (simplejwt) / Django DB sessions with header carrier | Django DB sessions, `Authorization: Session` | PROPOSED | Server-side revocation, immediate deactivation, no token storage, already installed |
| Library | django-allauth / hand-written adapter on requests + PyJWT | Hand-written adapter | PROPOSED (OQ-7) | Smaller surface, no templates/forms, API-first fit; PKCE and validation are explicit and testable |
| Role store | Entra groups in token / Django Groups | Django Groups | PROPOSED (OQ-3) | P5 forbids token-claims-only access; no new tables |
| User model | Swap `AUTH_USER_MODEL` / keep `User` + `EntraIdentity` | Keep `User` | PROPOSED | Swapping later is hard; identity table keeps vendor data in the adapter's module |
| Logout | Timely only / Entra end-session | Timely only + `prompt=select_account` | PROPOSED (OQ-5) | Avoids signing users out of unrelated Microsoft apps |
| Entra token retention | Store refresh token / discard | Discard | PROPOSED | Less to protect; trade-off in R-3 |
| Error envelope | RFC 9457 / custom | Custom D-11 shape | PROPOSED (D-23 OPEN) | Needed by the new endpoints; D-23 stays OPEN, shape is the documented one |

**Dependencies:** no new installs. Approval needed to *use* `requests`, `PyJWT`, `cryptography` (installed but unapproved, D-18) and to *remove* `django-allauth`, `djangorestframework_simplejwt`, `oauthlib` from `backend/requirements.txt` (OQ-7). Frontend: none.

## 9. Traceability Matrix
| Spec item | Plan section | Notes |
|---|---|---|
| US-1 / AC-1.1–1.5 | §4 start/complete, §5, §6, §7 login page | Account choice via `prompt=select_account`; tenant check |
| US-2 / AC-2.1–2.5 | §5 open redirect, §7 login page/layout/ProfileMenu | `/me/` feeds the shell |
| US-3 / AC-3.1–3.6 | §4 existing-endpoint changes, §5 deny-by-default and frontend gate | URL-enumeration test |
| US-4 / AC-4.1–4.7 | §3 models, §4 `/me/`, §5, `assign_role` command | Groups as roles; claims ignored |
| US-5 / AC-5.1–5.5 | §5 session, §6 config | 30 min idle / 8 h absolute (OQ-5) |
| US-6 / AC-6.1–6.4 | §4 logout, §7 handler | Origin check; server-side flush |
| US-7 / AC-7.1–7.5 | §4 errors, §7 error states | Uniform errors; no existence leak |
| US-8 / AC-8.1–8.2 | §3 AuthEvent, §5 audit | Fail-closed on sign-in |
| OQ-6 | §5 foundation hardening, §4 changes | Pending approval |

## 10. Testing Strategy
- **Backend service/unit (`manage.py test accounts`):** token validation with a locally generated RSA key and a stubbed JWKS (valid, bad signature, wrong `aud`, `iss`, `tid`, expired, wrong `nonce`, missing `oid`, `alg=none`); identity keyed by `(tid, oid)` not email (changed email, duplicate email); first-sign-in creates a user with no roles; inactive user refused; `next` sanitiser table; attempt single-use, expiry, wrong binding; session idle/absolute expiry; audit events written, no secrets in them.
- **API tests:** each endpoint's success and error contract including envelope and `Cache-Control`; every URL pattern is either on the public list or returns 401 unauthenticated; `system-info` 401/403/200; role change effective on the next request; logout invalidates the key; Entra failures map to 502/503 without leaking details.
- **Adapter tests:** mocked `requests` for discovery, JWKS, token endpoint (success, timeout, 5xx, malformed).
- **Frontend (`npm test`, `lint`, `typecheck`, `build`):** safe-redirect, cookie option builder, Origin check, `apiRequest` (forwarding, error mapping, timeouts), `/me` mapping, login-notice mapping, proxy redirect decision; existing tests (api-client, raw-colors, tokens, navigation) still pass. Route handlers are covered with mocked `fetch` where the Next.js runtime allows it.
- **Manual (owner-run, needs a real Entra app registration):** full sign-in, account chooser, deep-link return, wrong-tenant account, logout and back button, session timeout, role assignment via command. Recorded as executed or not executed in `validation.md` (P6). Not marked Passed without evidence.

## 11. Risks & Mitigations
- **R-1 Misconfigured app registration or redirect URI** → startup/first-use check with a secret-free log; documented owner steps (OQ-1).
- **R-2 Account takeover through email matching (nOAuth)** → identity keyed by `(tid, oid)`, tested (AC-4.1).
- **R-3 Microsoft-side disablement does not end Timely sessions until expiry** (no refresh token, no Graph) → absolute 8 h cap, immediate Timely-side deactivation, shorter lifetime available via env; Graph/revocation checks DEFERRED.
- **R-4 Zero-role users can sign in** → they can reach only `/me/`; all other APIs deny by default; Entra "Assignment required" reduces exposure (OQ-2).
- **R-5 No rate limiting (D-40)** on the two public endpoints → attempts are single-use, uniform errors, short expiry; limiting stays DEFERRED.
- **R-6 Hardcoded `SECRET_KEY` and `DEBUG`** → removed in this feature (OQ-6); the owner must set a new key.
- **R-7 Django admin keeps password login** (out of scope) → noted for a later decision.
- **R-8 Refactoring `client.ts` could regress the health card** → keep `getHealth` behaviour and run the existing api-client tests.
- **R-9 Session carried via server-to-server header means Django must stay unreachable from browsers' cross-site contexts** → no CORS, no cookie-based auth on API routes; deployment networking is OPEN (Constitution §3).

## 12. Constitution Check
| Principle | Compliant? | Notes |
|---|---|---|
| P1 Spec first, gates | Yes, with one flagged deviation | Spec was written as a file in one pass at the owner's request; no implementation or approval assumed |
| P2 Labelled decisions | Yes | All decisions PROPOSED; OPEN items are OQ-1 to OQ-8 |
| P3 Modular monolith | Yes | New `accounts` module proposed (D-22), one-directional dependency, no cross-module model imports |
| P4 Adapters | Yes | Entra only through `adapters/entra.py`; no Graph |
| P5 Security | Yes | Server-side authorisation; claims not trusted; no tokens in browser storage; secrets from env; diagnostics protected; audit events (retention DEFERRED) |
| P6 Evidence | Yes | Tests per AC; manual Entra checks reported separately and honestly |
| P7 Minimal footprint | Pending approval | No new installs; use of three installed packages and removal of three needs approval (OQ-7); no Docker/WSL/AI |
| P8 API-first | Yes | Django holds logic and data; Next.js relays three navigations (BFF register entry) and never touches the DB or Entra |

## 13. Change Log
| Date | Change | Reason | Approved by |
|---|---|---|---|
| 2026-10-13 | **Amendment A-1 (approved 2026-10-13, implemented 2026-10-13): the application adopts the existing registered Entra URI `<APP_ORIGIN>/api/auth/callback/azure-ad`.** Callback route, binding-cookie path, `proxy.ts` exemption and `next` sanitiser changed; no Auth.js/NextAuth/MSAL. See §14. §2 diagram, §5 binding-cookie and open-redirect bullets, §6 owner actions and §7 BFF table are read as amended by §14. | Owner cannot change the Entra registration; live sign-in returned to `/login` because no route exists at the registered URI | Project owner, 2026-10-13 |
| 2026-10-13 | Feature closed with the validation approval. Implementation notes reviewed by the owner (no plan change): `lib/auth/gate.ts` extraction (§14.2 item 4 delegates the exemption to it), profile-menu logout fix, login-page `<Suspense>`, sidebar curve CSS; recorded in `validation.md` §5. Limitations in `validation.md` §6. | Owner validation approval | Project owner, 2026-10-13 |

## 14. Amendment A-1 — callback route does not match the registered redirect URI (APPROVED and implemented 2026-10-13)

**Observed (2026-10-13).** Owner clicks "Sign in with Microsoft", signs in at Microsoft, and lands on `/login` with no message. The audit log shows only `login_started` (no `login_refused`, no `login_succeeded`): Django's `login/complete` is never called.

**Evidence (executed).**
| Item | Finding |
|---|---|
| Authentication library | Custom BFF as approved (D-55): Django (`requests`, `PyJWT`, `cryptography`, `accounts/adapters/entra.py`) does the OAuth code + PKCE flow; Next.js has three Route Handlers only. **No Auth.js / NextAuth / MSAL** exists in `frontend/package.json`, `node_modules` or source (0 matches). |
| Entra registered redirect URI (owner) | `http://localhost:3000/api/auth/callback/azure-ad` (the Auth.js "azure-ad" convention, used by the owner's other app) |
| `MICROSOFT_REDIRECT_URI` (backend, running Django) | `http://localhost:3000/api/auth/callback/azure-ad` |
| Runtime authorization request `redirect_uri` | `http://localhost:3000/api/auth/callback/azure-ad` — **matches Entra**, so Microsoft accepts the sign-in and redirects there |
| Application callback handler | Only `GET /auth/callback` exists (`app/auth/callback/route.ts`). There is **no** route at `/api/auth/callback/azure-ad`. |
| Request to the registered URI | `GET /api/auth/callback/azure-ad?code=…&state=…` → `307` to `/login?next=%2Fapi%2Fauth%2Fcallback%2Fazure-ad%3F…` |

**Root cause.** The redirect URI sent to and registered with Microsoft points at a route the application does not implement. `proxy.ts` treats it as an unauthenticated page request (its matcher excludes only `auth/`, not `api/auth/`) and redirects to `/login`. Django never receives the code, the attempt is never consumed, and no message is shown because the redirect carries no `error` key. Earlier in validation the URI was `/auth/callback` (matching the handler) but did not match Entra (`AADSTS50011`). The two sides were never aligned.

**Constraint from the owner (2026-10-13).** The Entra redirect URI **cannot be changed** and stays `<APP_ORIGIN>/api/auth/callback/azure-ad`. The application must be adapted. Auth.js, NextAuth and MSAL are **not** introduced, and custom callback handling is not mixed with them (D-55, P7, P8).

**Superseded.** The earlier "Option 1: register `/auth/callback` in Entra" is no longer available. Spec OQ-1, plan §6/§7 and tasks T0/T13 (which named `/auth/callback`) are corrected by the changes below.

### 14.1 Full flow, with every place the callback path or URL is known

```
Django  start_login ── MICROSOFT_REDIRECT_URI (env) ──▶ authorization_url (redirect_uri=…)   [backend/config/settings.py:163, adapters/entra.py:61]
Next BFF GET /auth/login ──302 Entra──  + Set-Cookie timely_login; Path=<LOGIN_COOKIE_PATH>  [lib/auth/flow.ts, cookies.ts:7]
Entra ──302 <registered URI>?code&state──▶ browser ──GET──▶ proxy.ts ──▶ route handler       [proxy.ts matcher, app/auth/callback/route.ts]
Next BFF handleCallback ──POST login/complete/──▶ Django (state+binding+PKCE+single use)     [lib/auth/flow.ts, lib/api/accounts.ts:71]
Django token request (same redirect_uri again, required by Entra) ──▶ Entra                  [adapters/entra.py:133,180]
```

| # | Where | What is hardcoded or configured | Environment-specific? | Problem today |
|---|---|---|---|---|
| 1 | `backend/.env` `MICROSOFT_REDIRECT_URI` | The full URI sent to Entra | **Yes** (origin differs per environment) | None. Already the single backend source. Read once in `settings.py:163`; `entra.py` uses it for the authorize and token requests. Value is already `…/api/auth/callback/azure-ad` |
| 2 | `frontend/.env.local` `APP_ORIGIN` | Frontend origin | **Yes** | None |
| 3 | `frontend/app/auth/callback/route.ts` | Route location (file-system routing) | No (same in every environment) | **Root cause.** Serves `/auth/callback`, not the registered path |
| 4 | `frontend/lib/auth/cookies.ts:7` `LOGIN_COOKIE_PATH = "/auth/callback"` | Binding-cookie `Path` | No | Would not be sent to `/api/auth/callback/azure-ad` (Path mismatch) → `invalid_attempt` |
| 5 | `frontend/proxy.ts` matcher | Excludes `auth/` only | No | `/api/auth/callback/azure-ad` is treated as a protected page and redirected to `/login` **before the OAuth response is processed**. The matcher must be a literal, so it cannot import a constant |
| 6 | `frontend/lib/auth/safe-redirect.ts:13` and `backend/accounts/redirects.py:14` | `next` may not be `/login` or `/auth/*` | No | `next=/api/auth/…` would be accepted. Must also be refused |
| 7 | `frontend/lib/api/accounts.ts` `/v1/accounts/auth/*` | Django API paths (relative to `API_URL`) | No (base URL from `API_URL`) | None |
| 8 | `frontend/app/login/page.tsx`, `profile-menu.tsx` | `/auth/login`, `/auth/logout` (own pages) | No | None. Unrelated to the callback |
| 9 | Tests and docs | `http://localhost:3000/auth/callback` in `tests/auth.test.mjs`, `accounts/tests/helpers.py`, plan, spec OQ-1, tasks T0/T13, `docs/architecture.md` §3 BFF register, `.env.example` comments | n/a | Updated with the change |

There are no hardcoded Entra authority URLs except the fixed host `login.microsoftonline.com` (a constant by design, plan §6). No URL is hardcoded in `settings.py`.

### 14.2 Change made (smallest safe set; implemented 2026-10-13)
Principle: the *origin* comes from the environment (`APP_ORIGIN`, `MICROSOFT_REDIRECT_URI`); the *path* is application structure and is defined **once** in one module, then imported everywhere it is needed.

1. **New** `frontend/lib/auth/paths.ts` (plain module, no secrets): `export const AUTH_CALLBACK_PATH = "/api/auth/callback/azure-ad";`. The single source for the path in code.
2. **Move** the handler: `app/auth/callback/route.ts` → `app/api/auth/callback/azure-ad/route.ts` (still `GET` only, still `handleCallback`). The old `/auth/callback` is **removed, not aliased**, so there is exactly one public callback. File-system routing cannot read a constant, so a test asserts that the file exists at the path derived from `AUTH_CALLBACK_PATH` (drift guard 1).
3. `lib/auth/cookies.ts`: `LOGIN_COOKIE_PATH = AUTH_CALLBACK_PATH` (the cookie stays scoped to exactly the callback path, never wider).
4. `proxy.ts`: before the session-cookie check, `if (request.nextUrl.pathname === AUTH_CALLBACK_PATH) return NextResponse.next();` — an **exact-path** exemption using the constant. The matcher is unchanged (no duplicated literal, no `api/auth/` wildcard). Result: the OAuth response is always processed by the handler and never redirected to `/login` first.
5. **Drift guard 2** in `handleLoginStart`: parse `redirect_uri` from the `authorization_url` returned by Django and require it to equal `APP_ORIGIN + AUTH_CALLBACK_PATH`. On mismatch, fail closed with `/login?error=unavailable` and a secret-free log line (`[auth] MICROSOFT_REDIRECT_URI does not match the callback route`). A wrong env value is now reported at the first click instead of as a silent bounce after Microsoft.
6. `safe-redirect.ts` and `accounts/redirects.py`: also refuse `next` beginning with `/api/auth` (table tests updated in both languages).
7. Django: **no code change.** `MICROSOFT_REDIRECT_URI` stays the single env-driven source. `backend/.env.example` and `frontend/.env.example` comments updated to the new URI. The `accounts/tests/helpers.py` fixture URI is aligned.
8. Docs: `docs/architecture.md` §3 BFF register row renamed to `GET /api/auth/callback/azure-ad` (needs the owner's approval, listed in tasks); `frontend/README.md` only if it names the old path (it does not).

**Considered and rejected**
| Alternative | Why not |
|---|---|
| Auth.js / NextAuth / MSAL | Owner constraint; breaks D-55 and P8, adds an unapproved dependency (P7) |
| `app/api/auth/[...nextauth]` or `[provider]` catch-all | Reserves Auth.js's namespace and would accept any provider string |
| `next.config` rewrite `/api/auth/callback/azure-ad → /auth/callback` | Keeps two public entry points; `proxy.ts` runs before rewrites and still needs the exemption; the cookie `Path` must still match the browser-visible URL, so no work is saved |
| Wildcard exemption `api/auth/*` in `proxy.ts` | Opens every future `/api/auth/*` route to cookie-less access |
| Change the URI in Entra | Not permitted for the owner |

### 14.3 Security implications
- **Public surface:** unchanged in size. One public callback route moves from `/auth/callback` to the registered path; the old path disappears. The exemption in `proxy.ts` is for that exact path only and does not weaken the proxy for any other URL. `proxy.ts` is not a security boundary (plan §5); Django and `requireUser()` still enforce access.
- **Callback protection is unchanged:** `state` (hashed, single use, 10 min), `timely_login` binding (HttpOnly, SameSite=Lax, constant-time hash compare), PKCE S256, `nonce`, `tid`. Login CSRF and fixation (AC-1.4) behave as before. The cookie `Path` is exactly the callback path, so it is not sent to any other route.
- **SameSite=Lax cookie on a cross-site redirect:** Microsoft returns the browser with a top-level `GET` (`response_mode=query`), for which Lax cookies are sent. Verified by a local cookie-replay test, and by the owner's live run.
- **Open redirect:** `next` cannot target `/api/auth/*` (item 6), so the callback cannot be chained into a loop.
- **Reserved namespace:** `/api/auth/*` is the Auth.js convention. The route is a single exact path, not a catch-all. If Auth.js were ever adopted, this feature would need re-planning.
- **Misconfiguration is fail-closed:** a mismatch between env and route is refused at `login/start` (drift guard 2). Entra still rejects an unregistered `redirect_uri` (`AADSTS50011`).
- **No new secrets, dependencies or logging of codes/state/cookies.** The origin check and session cookie are unchanged.

### 14.4 Tests (written and executed; results in `validation.md` §1b)
| Test | Proves |
|---|---|
| `lib/auth` unit: `AUTH_CALLBACK_PATH` equals the Entra registered path; `LOGIN_COOKIE_PATH` equals it; the Set-Cookie from `handleLoginStart` carries that `Path` | single source, cookie scoping |
| File-existence test: `app/api/auth/callback/azure-ad/route.ts` exists and `app/auth/callback/` does not | drift guard 1, one public callback |
| `handleLoginStart` with a Django response whose `redirect_uri` differs from `APP_ORIGIN + AUTH_CALLBACK_PATH` → `/login?error=unavailable`, no cookie set | drift guard 2 |
| `handleCallback` at the new URL (existing cases moved): success, missing code/state/cookie → `invalid`, `error=access_denied` → `not_completed`, Django error codes → mapped keys | callback behaviour unchanged |
| Proxy decision: exact `AUTH_CALLBACK_PATH` with no cookie → pass through; `/api/auth/callback/azure-ad/x`, `/api/auth/other`, `/reports` with no cookie → redirect to `/login` | exact-path exemption only |
| `safeNextPath` / `safe_next_path` table: `/api/auth/callback/azure-ad`, `/api/auth/x` → `/` (frontend and backend) | open redirect, loop prevention |
| Backend: existing `accounts` suite (50 tests) still passes with the fixture URI aligned | no backend regression |
| Live smoke (curl, executed after implementation): `GET /api/auth/callback/azure-ad?code=x&state=y` without cookies → `302 /login?error=invalid` (not `/login?next=…`); with a valid binding cookie → reaches Django (`not_completed`/`invalid`, an audit event is written); `GET /auth/callback` → 404 | the original bug is fixed |
| **Owner live check (Entra, browser):** sign-in → home page, first-time user created, `assign_role`, logout | AC-1.2, AC-2.1, AC-2.2 move from Not executed to Passed only with this evidence |

### 14.5 Impact on documents
Spec: OQ-1 corrected, new AC-1.6. Tasks: T12/T13 amended, new T20–T26. Validation: new rows and AC-1.6. Architecture register and `.env.example` comments updated in T24. Implemented after the owner's separate instruction (D-6).

## 14a. Amendment A-1 status
Approved by the project owner on 2026-10-13 and implemented (tasks T20–T26, evidence in `validation.md` §1b). Feature 002 closed 2026-10-13.

---
**Status:** Approved · **Feature closed:** 2026-10-13 · **Approved by:** Project owner · **Date:** 2026-10-13 (incl. amendment A-1)
