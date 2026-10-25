# Kaizora

Project delivery + client operations, built as an API-first modular monolith.
This repository contains the development/UI foundations and web login, app shell
and logout, organizations/memberships (0003), roles/permissions (0004), account preferences (0005), clients/contacts (0006), people/teams (0007) and projects foundation (0008), plus direct member/resource selection and project workforce (0009). Later operational and financial workflows remain unimplemented. `example-sdd/` is preserved
Timely reference documentation, not active project instructions.

## Layout

- `backend/`: Django, DRF, PostgreSQL, Admin, domain packages and tests.
- `frontend/`: React + TypeScript + Vite, generated API types and authenticated app shell.
- `docs/constitution.md`: specification-driven development rules.
- `docs/architecture/`: module ownership and architectural decisions.
- `docs/specs/`: numbered specs, design, tasks and verification.
- `docs/api/openapi.yaml`: generated API contract.
- `scripts/`: architecture validation.

## Prerequisites

Python 3.12–3.14, Node 22.12+ (Node 24 recommended), Docker Compose.
Use Bash commands below from the repository root.

## Setup

```bash
cp backend/.env.example backend/.env  # first setup only; preserve existing values
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
npm ci --prefix frontend
docker compose up -d --wait postgres
backend/.venv/bin/python backend/manage.py migrate
backend/.venv/bin/python backend/manage.py createsuperuser
```

PostgreSQL is bound to `127.0.0.1:55432`. If you change it, update both Compose
and `backend/.env`. Docker credentials are development-only. Do not reuse them
for production. No default administrator account is created.

## Run (separate terminals)

```bash
backend/.venv/bin/python backend/manage.py runserver 127.0.0.1:8000
npm run dev --prefix frontend
```

Web: http://localhost:5173 · Admin: http://localhost:8000/admin/
API liveness: http://localhost:8000/api/v1/health/live/
API readiness: http://localhost:8000/api/v1/health/ready/
API docs (DEBUG, staff login required): http://localhost:8000/api/docs/
The docs page loads Swagger assets from its default CDN.
The app now opens a session-protected shell. API liveness does not imply database readiness.

## Verify

```bash
python3 scripts/check_boundaries.py
python3 -m unittest discover -s scripts -p 'test_*.py'
backend/.venv/bin/ruff check backend scripts
backend/.venv/bin/ruff format --check backend scripts
backend/.venv/bin/python backend/manage.py check
backend/.venv/bin/python backend/manage.py makemigrations --check --dry-run
backend/.venv/bin/pytest -c backend/pyproject.toml backend/tests
npm run build --prefix frontend
```

Database tests require PostgreSQL and a local role allowed to create test databases;
the Compose development role has this permission. Tests use a separate test database.

## Update API contract

```bash
backend/.venv/bin/python backend/manage.py spectacular --file docs/api/openapi.yaml --validate --fail-on-warn
npm run api:types --prefix frontend
npm run typecheck --prefix frontend
```

Review schema/type changes together. Mobile apps will consume the same `/api/v1/`
contract. Web application login is implemented. Native mobile authentication is not implemented yet.
Web mutations must use CSRF-protected sessions; native auth needs its own spec.

## SDD workflow

Start at [the documentation index](docs/README.md), then read the constitution,
workflow and feature index. Reusable templates live in `sdd-templates/`. Specify each feature's
business rules, interface/API contract and acceptance tests before implementation.
Do not import another module's models/services directly; use its `interfaces.py`.
Billing, approvals and historical corrections must use the same domain use cases
from Admin and DRF when implemented.

## Dependencies and lifecycle

Python input ranges are in requirements*.in; requirements*.txt lock the verified
environment. npm uses package-lock.json. Re-resolve intentionally, run all checks,
and review dependency changes before adopting updates.

`docker compose stop` stops local PostgreSQL while keeping data. Do not use
`docker compose down -v` unless you intentionally want to erase the development DB.
This is not a production deployment; tenancy, production auth, HTTPS hosting,
backups, monitoring and business modules need later specifications and verification.

## App login and shell

Open http://localhost:5173/login and sign in with an existing active Django user's
**username and password**, including the account created with `createsuperuser`.
No default credentials or signup flow are provided. Staff status is not required.

- `/app`: protected home and responsive navigation.
- `/app/account`: editable profile and theme/timezone preferences; username/email read-only.
- Account menu → Sign out: ends the Django session and returns to login.
- `/__ui`: development-only component showcase (no authentication required).

Admin and app share Django's session on the same hostname. Signing out of one
ends that session in both; an Admin session may already sign you into the app.
Use the same hostname consistently (`localhost` or `127.0.0.1`) to avoid separate
cookie jars. No new migration is needed for this feature. Provision/edit users
through Django Admin; existing database migrations must already be applied.

API: GET `/api/v1/auth/session/`, POST `/api/v1/auth/login/`, POST
`/api/v1/auth/logout/`. Unsafe requests require X-CSRFToken, obtained from the
session response. Web session auth is implemented; native mobile auth is deferred.

Frontend regression tests: `npm test --prefix frontend`. Auth/CSRF backend tests:
`backend/.venv/bin/pytest -c backend/pyproject.toml backend/tests` (creates an isolated
PostgreSQL test database; the configured DB user needs test-database permissions).

Before production: serve the SPA and API under one origin, configure HTTPS and
secure cookies, deep-link fallback to index.html, and a shared cache / proxy-aware
rate limit. The current 10/minute login limit uses Django's local-memory cache.
See `docs/specs/0002-session-shell/` for scope, contracts and verification.

## Organizations and membership (0003)

Open `/app/organizations` from the sidebar. Organization settings use
`/app/o/<organization-uuid>/settings`. No default organization or membership is created.
The additive `organizations.0001_initial` migration was applied to the configured local
DB during implementation. On another environment, run `python backend/manage.py migrate`.

Use **Organizations → Create organization** in the app, or **Organizations → Add** in
Django Admin. Both accept the first owner’s existing username. CLI below is optional.

To provision an organization, use an existing active operator with the Django permission
`organizations.bootstrap_organization` (an active superuser qualifies) and an existing
active owner. IDs are the UUIDs shown in Django Admin user detail URLs. With your virtual
environment active, from the repository root:

```bash
python backend/manage.py provision_organization \
  --actor-id <operator-user-uuid> \
  --owner-id <owner-user-uuid> \
  --name "Your organization" \
  --timezone Asia/Dhaka
```

Replace the angle-bracket placeholders before running. The same operation is available
at POST `/api/v1/organizations/` with session CSRF protection. Operator permission does
not grant read access to organizations they do not belong to.

The 0004 live permission policy now enables member and role management in organization
settings. Owners can add existing users by username, create roles (or use presets), assign
or revoke them, suspend/end/reactivate memberships, and transfer ownership with a reason.
Basic members see their own access summary. Non-owners need explicit permissions; the
assignment picker needs memberships.read, roles.read and roles.assign. Dropdown choices
come from the currently displayed Members/Role pages. History remains after access ends.
Organization/Member/Role/Assignment Django Admin forms now call the same domain commands;
audit events and raw permission rows remain read-only. Account/login/logout need no organization membership.

You can also provision by username (use your actual existing operator and owner accounts):

```bash
python backend/manage.py provision_organization \
  --actor-username admin \
  --owner-username admin \
  --name "Your organization" \
  --timezone Asia/Dhaka
```

An active superuser can provision; this does not make them an owner of other organizations.
The additive identity.0002 role migration has been applied locally. Project-specific role assignment is implemented in 0008; other future business modules remain separate.

See [0003 verification](docs/specs/0003-organizations-membership/verification.md) for
actual checks and limits. No new application server needs to be run.

See [roles and membership usage](docs/roles-membership-usage.md) and [0004 verification](docs/specs/0004-roles-permissions/verification.md).


## End-user guide

Open **User guide** in the app footer, or visit `http://localhost:5173/user-guide/`.
The Bengali guide includes setup, example roles, UI and Django Admin workflows,
two-organization walkthrough, lifecycle/history rules and troubleshooting.
It supports section search, mobile layout and Print / Save as PDF.
Canonical source: [user guide](frontend/public/user-guide/index.html).
Maintenance and coverage: [guide index](docs/user-guide/README.md).
Every user-facing feature must update the guide in the same delivery.
