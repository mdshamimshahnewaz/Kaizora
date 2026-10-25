# Copilot instructions for Kaizora

## Build, test, and lint

Run commands from the repository root. Backend commands use the checked-in virtual
environment; database-backed tests require PostgreSQL and a role allowed to create
test databases.

```bash
# Backend and repository checks
python3 scripts/check_boundaries.py
python3 -m unittest discover -s scripts -p 'test_*.py'
backend/.venv/bin/ruff check backend scripts
backend/.venv/bin/ruff format --check backend scripts
backend/.venv/bin/python backend/manage.py check
backend/.venv/bin/python backend/manage.py makemigrations --check --dry-run
backend/.venv/bin/pytest -c backend/pyproject.toml backend/tests

# Frontend
npm run lint --prefix frontend
npm run check:ui --prefix frontend
npm run typecheck --prefix frontend
npm test --prefix frontend
npm run build --prefix frontend
```

Run one backend test by node ID, for example:

```bash
backend/.venv/bin/pytest -c backend/pyproject.toml \
  backend/tests/test_projects.py::test_private_project_creation
```

Run one frontend test file or named test:

```bash
npm test --prefix frontend -- src/features/organizations/organization-pages.test.tsx
npm test --prefix frontend -- src/features/organizations/organization-pages.test.tsx \
  -t "offers account access without inventing an organization"
```

When changing an API schema, regenerate and verify both sides of the contract:

```bash
backend/.venv/bin/python backend/manage.py spectacular \
  --file docs/api/openapi.yaml --validate --fail-on-warn
npm run api:types --prefix frontend
npm run typecheck --prefix frontend
```

## Architecture

Kaizora is a single-deployment Django/DRF modular monolith with PostgreSQL and a
React/TypeScript/Vite browser application. The request path is browser → versioned
`/api/v1/` JSON API → owning Django module's commands/queries → PostgreSQL. Django
Admin is an operator surface, not a second business-logic layer. Web sessions use
Django cookies; unsafe requests require CSRF. Native mobile authentication is not
implemented.

Installed domain modules include `identity`, `system`, `organizations`, `clients`,
`resources`, and `projects`. Other directories under `backend/modules/` reserve
future boundaries; their presence does not mean those business capabilities exist.
Each module owns its data writes. Cross-module calls go through the owning module's
`interfaces.py`; keep models and querysets private. `scripts/check_boundaries.py`
enforces the ordinary static-import rule.

The frontend groups screens and API wrappers under `frontend/src/features/`.
Components use those wrappers and the shared typed `openapi-fetch` client in
`frontend/src/api/client.ts`. API types in `frontend/src/api/schema.d.ts` are
generated from `docs/api/openapi.yaml`; do not edit generated types by hand.

## Repository-specific conventions

- Before feature work, follow `docs/constitution.md` and `docs/sdd-workflow.md`.
  Feature artifacts live in sequential `docs/specs/NNNN-slug/` directories
  (`spec.md`, `design.md`, `tasks.md`, `verification.md`). Keep planned checks
  distinct from executed evidence; do not imply owner approval or production
  readiness.
- A user-facing feature includes the end-user guide in
  `frontend/public/user-guide/index.html`, its coverage map in
  `docs/user-guide/README.md`, and links plus actual guide checks in that feature's
  `verification.md`. Cover App UI and applicable Django Admin workflows.
- Put business rules, permission checks, validation, transactions, and history in
  module-owned commands/queries exposed by `interfaces.py`. Revalidate the actor
  and organization scope server-side. API views and Django Admin mutations should
  call the same domain operations; use command-backed Admin forms rather than
  unrestricted model saves. Keep audit/history records read-only where specified.
- API routes are versioned, end in `/`, and use snake_case fields. DRF session
  authentication and CSRF behavior are endpoint contracts; do not assume every
  403 means an expired session or replace documented error/status behavior.
- In the UI, reuse shared shadcn components, Tailwind semantic tokens, and Lucide
  icons. Feature tests generally mock the API boundary; treat them as UI behavior
  evidence, not proof of a live browser/backend integration.
- Backend settings load `backend/.env` and require PostgreSQL. Keep credentials
  out of frontend configuration and bundles. Follow `README.md` for local setup;
  avoid `docker compose down -v` unless intentionally deleting local database data.

For detailed ownership, API, frontend, and delivery rules, see
`docs/architecture/`, `docs/api-conventions.md`, `docs/frontend-api-client.md`,
`docs/frontend-ui-rules.md`, and the root `AGENTS.md`.
