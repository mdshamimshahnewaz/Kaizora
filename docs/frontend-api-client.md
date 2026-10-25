# Frontend API client rules

Kaizora is a browser SPA, not a server-rendered frontend. The implemented client is
[`src/api/client.ts`](../frontend/src/api/client.ts): typed `openapi-fetch` with an
empty base URL and `credentials: same-origin`. Vite proxies `/api` in development;
production routing must keep browser and API under the configured same origin.

## Boundaries
Use the shared client. Feature wrappers live under `src/features/<feature>/api.ts`
(as authentication does today). Components consume feature wrappers/providers rather
than constructing backend URLs or duplicating transport calls. No database driver,
credential, ORM or server-only/BFF assumption belongs in the frontend.
Generated types live in `src/api/schema.d.ts`; they provide compile-time checks,
not runtime validation. Specify runtime guards for untrusted complex responses when
needed. Do not claim a universal validator, timeout or error wrapper exists today.

## Sessions and errors
Auth session reads use no-store. Obtain a fresh CSRF token before login/logout,
keep it in memory, and send X-CSRFToken for unsafe session mutations. Session IDs
remain HttpOnly cookies. Clear private UI on confirmed logout; report network failures
without claiming server revocation. The provider checks on focus and periodically,
and sequences responses to prevent stale reads replacing newer session state.

Distinguish unavailable backend from anonymous session. Interpret status and payload
according to each endpoint; blanket redirect-on-403 would mishandle CSRF errors.
Show actionable loading, retry, empty and permission states without exposing internals.
Private caches, if added later, must be scoped and cleared on identity/scope changes.

## New feature transport design
Specify cancellation/timeouts, safe retries, concurrency and invalid-response handling.
Do not automatically retry a financial mutation without server idempotency guarantees.
Use bounded pagination and allowed server filters, not downloading all rows to filter
in the browser. Test success, validation, denied access, network failure and stale
responses where applicable. Existing frontend app tests mock the API boundary;
record separately which flows have real browser/backend evidence.
