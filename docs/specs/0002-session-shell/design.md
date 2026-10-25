# Design

Identity owns authentication; views use Django authenticate/login/logout and DRF
serializers. No other domain module is needed and no schema migration is required.

| Endpoint | Request | Response |
| --- | --- | --- |
| GET /api/v1/auth/session/ | session cookie (optional) | 200 {user: User or null, csrf_token: string} |
| POST /api/v1/auth/login/ | {username, password}, X-CSRFToken | 200 session payload; 400 invalid credentials/input; 403 CSRF; 429 throttled |
| POST /api/v1/auth/logout/ | X-CSRFToken | 204; 403 CSRF. Anonymous logout is idempotent. |

User exposes id, username, display_name, email only. Session IDs remain HttpOnly,
SameSite=Lax, secure outside DEBUG. Tokens stay in memory, never localStorage.
Session lifetime: Django's existing default; backend remains authority. No persistent
"remember me" option in this increment. Session snapshot is no-store.

Explicit csrf_protect wraps dispatch: anonymous DRF login must not bypass CSRF.
Login throttle is per IP, 10/minute; local-memory cache suits local development.
Production needs a shared cache and trusted proxy/rate-limit configuration.
Frontend gets a fresh CSRF token before mutations (other tabs may rotate it).
Logout only clears UI on confirmed success. A 60-second/focus session check reconciles
other tabs and expiry, with request sequencing to discard stale read responses.

BrowserRouter routes: / -> /app, /login, /app (Home), /app/account, protected
not-found under /app; global not-found offers home. Login returns to a validated
/app-relative route only. No arbitrary redirect URL. Providers are not mounted
for /__ui. Same-origin Vite /api proxy preserved; production must route /api to
Django and serve index.html for frontend deep links.

References: https://www.django-rest-framework.org/api-guide/authentication/
https://reactrouter.com/start/declarative/installation
