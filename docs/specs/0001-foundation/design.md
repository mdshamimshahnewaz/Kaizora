# Foundation contracts

## HTTP
GET `/api/v1/health/live/`: public, no auth, no database dependency, HTTP 200.
GET `/api/v1/health/ready/`: public, PostgreSQL SELECT 1, HTTP 200 or 503.
Both return `status` (ok/unavailable), `service` (kaizora-api), `api_version` (v1).
Readiness checks connectivity only, not migration freshness or feature availability.

`/admin/` uses Django staff authentication. `/api/schema/` and `/api/docs/` are
registered only in DEBUG mode and require staff sessions. CLI schema export works
without a browser session. Other API endpoints inherit IsAuthenticated by default.

## Python
`modules.system.interfaces.liveness() -> HealthStatus`
`modules.system.interfaces.readiness() -> HealthStatus`
HealthStatus is an immutable dataclass. Views adapt the result into JSON.
The system health contract contains no business data and needs no actor scope.

## Frontend
React -> openapi-fetch (generated types) -> Vite `/api` proxy -> DRF.
Production reverse-proxy hosting and mobile authentication are later specs.

## Local infrastructure
PostgreSQL 17, persistent Docker volume, loopback host port 55432 to avoid an
existing host PostgreSQL on 5432. Credentials are local-development values only.
Django reads backend/.env; checked-in .env.example contains no production secrets.
