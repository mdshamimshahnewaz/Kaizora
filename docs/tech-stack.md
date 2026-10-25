# Technology stack and dependency policy

Updated: 2026-10-18. These are manifest ranges and repository facts, not a fresh
runtime audit or a claim about latest upstream releases. Exact resolutions live in
lockfiles. This documentation update installs and upgrades nothing.

| Layer | Current declaration / source |
| --- | --- |
| Backend | Django >=5.2.8,<5.3; DRF >=3.16,<3.17; Python guidance 3.12–3.14 |
| Database | PostgreSQL only; psycopg 3; django-environ configuration |
| API schema | drf-spectacular; generated OpenAPI; openapi-typescript/openapi-fetch |
| Web | React 19, TypeScript 5.9, Vite 7, React Router 7; Node >=22.12.0 |
| UI | shadcn components/Radix, Tailwind 4, Lucide, Geist font, Sonner |
| Specialized installed libraries | TanStack Table, free SVAR React Gantt, @dnd-kit/react, Recharts |
| Forms/utilities | React Hook Form, Zod, resolvers, date-fns, clsx, tailwind-merge, CVA |
| Verification | pytest, Ruff, boundary checks; Vitest/Testing Library, ESLint, TypeScript |

Sources: [backend ranges](../backend/requirements.in),
[backend lock](../backend/requirements.txt), [frontend manifest](../frontend/package.json),
[npm lock](../frontend/package-lock.json), [UI dependency notes](../frontend/docs/design-system.md).
Next.js is not part of this application. Specialized dependencies do not imply
completed tables, Gantt screens, reporting or business forms.

Use npm and the existing lockfile; use Python requirement input/lock files together.
For a change, record purpose, supported versions, license/commercial-use restrictions,
free versus paid boundaries, alternatives and affected checks. Do not add a competing
UI framework or icon pack. Do not assume a license claim for a new version from an
older verification. Never require paid Gantt functionality without a separate decision.

Backend configuration lives in `backend/.env`; current settings read `DATABASE_URL`
and `DJANGO_*` keys. Use `backend/.env.example` and the root README for setup.
Separate `DB_NAME`/`DB_HOST` keys are not consumed by current settings. Never place
PostgreSQL credentials in frontend env. Any Vite-exposed setting is public bundle data.
Local PostgreSQL or the provided Compose service can be used; match the URL to the
chosen instance. Do not overwrite an existing environment file.
