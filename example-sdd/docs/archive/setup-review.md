# Project setup review and implementation plan

## Scope and approach

The initial setup review was completed without editing application files. At the user's request, this plan was copied to the project root. The user subsequently approved tooling fixes and a minimal frontend-to-Django health connection. Authentication and deployment-specific changes remain deferred.

## Current progress

- Completed: aligned `eslint-config-next` to Next 16.4.0, added repeatable lint/typecheck/test commands, and updated dependencies through npm.
- Completed: added a server-only `API_URL`, a non-secret `.env.example`, and the corresponding ignore exception. The existing public variable is preserved locally but no longer used by the homepage.
- Completed: added `lib\api\client.ts` and a request-time health UI with Suspense, a five-second timeout, response validation, explicit error logging, and healthy/unavailable states.
- Verified: lint, generated TypeScript checks, API helper tests, two database-independent DRF contract tests, and the production build pass.
- Verified: production HTTP responses show healthy for the actual Django service and unavailable for an unreachable backend; generated Tailwind styles are served correctly, and the backend URL is absent from client JavaScript.
- Tailwind and Next caching configuration were retained because they work in the production build. No CORS middleware was necessary for server-to-server communication.
- Temporary production smoke-test servers were stopped. Existing development services were not stopped.
- Completed: moved the existing frontend Git repository to the project root, preserving HEAD and commit history. Both directories now resolve to the same repository root. Added root ignore rules for backend environment files, virtualenvs, Python caches, local databases and generated output.
- Repository migration: original tracked frontend files are staged as path relocations under `frontend`; existing working edits remain unstaged. Backend, root plan and newly created frontend files remain untracked until explicitly staged. No commit or push was made.
- A recovery copy of the original frontend Git metadata is retained outside the project in the session `files\frontend-git-before-monorepo` directory. Earlier commits retain their original frontend-root paths; the staged relocation introduces the monorepo layout without rewriting history.
- Before staging backend settings, replace the hardcoded development secret with environment-based configuration; ignoring `.env` does not protect values embedded in source.
- Pending: SDD artifacts, hosting/auth decisions, production backend hardening, browser automation and CI. This is a local integration milestone, not a production-readiness claim.

The findings below are the original pre-implementation inspection snapshot; the progress above supersedes findings about missing API integration or broken lint tooling.

## Immediate next steps

1. Define `specs\constitution.md` and `specs\frontend-api-health\spec.md` with the health response contract, healthy/unavailable UI behavior, timeout/error rules, and acceptance criteria.
2. Decide whether root, backend, and frontend will share one Git repository or use separate repositories before adding tracking; protect backend secrets and generated files first.
3. Align `eslint-config-next` with Next 16.4.0 and restore the lint gate.
4. Define the server-only API URL, implement the smallest health-status integration, and verify healthy and unavailable behavior.

The local tooling and health integration steps are complete. Discuss authentication next; hosting-specific hardening and further implementation require their own decisions.

The approved planning scope is setup hardening and the first working API connection. Product features are deferred. SDD means spec-driven development. Hosting and authentication are undecided; recommendations must not silently choose either.

Recommended approach: retain the existing root-level frontend `app` directory and root import alias, restore working lint tooling, specify the API contract, and implement a server-first health-status UI in a later approved implementation. Use a server-only backend URL for that path. Add browser-facing proxy routes or direct-browser CORS only when an actual interactive feature requires them.

## Inspection scope and evidence

Actual project root:
`C:\Users\Shamim Shahnewaz\OneDrive - SEBPO\Documents\01_Development\django\timely-DRF`

Inspected frontend dependency manifests, configuration, environment file, Git ignore/tracking rules, App Router files, installed dependency versions, generated development CSS, and relevant documentation bundled with installed Next.js.

Inspected backend dependency manifest, Django settings, URL configuration, views, models, test stub, and environment variable names. Secret values are intentionally omitted from this report.

Read-only checks:

| Check | Result | Limitation |
| --- | --- | --- |
| Installed packages | Next 16.4.0; React and React DOM 19.3.0; TypeScript 5.9.3; ESLint 9.39.5; eslint-config-next 14.2.35; Tailwind and its Turbopack loader 4.3.3 | Confirms local installation, not a clean production installation |
| TypeScript | `tsc --noEmit --incremental false` succeeds | Generated Next development types already exist; fresh-build type generation remains to be checked |
| ESLint | Fails before linting with module-resolution error for `eslint-config-next/core-web-vitals` | Next 14 config package is incompatible with the current Next 16-style flat configuration |
| Frontend HTTP | Existing service at `http://localhost:3000` returns HTTP 200 | Does not prove a production build or browser interaction |
| DRF health | Existing service at `http://127.0.0.1:8000/api/health/` returns HTTP 200 and `{"status":"ok"}` | cURL is not subject to browser CORS |
| Browser-origin response | Health response to `Origin: http://localhost:3000` has no `Access-Control-Allow-Origin` | Direct cross-origin browser reads are not enabled |
| Django normal check | Passes | Not a deployment or database readiness guarantee |
| Django deployment check | One error and seven warnings | Console email backend, development secret, debug, hosts, TLS/HSTS and cookie settings |
| Tailwind | Existing development CSS contains generated utility rules such as `.flex` and `.max-w-3xl` | Production CSS generation not verified |
| Git status | Frontend retains pre-existing modifications to `app/page.tsx`, `package.json`, and `package-lock.json` | These changes must not be reverted |

No dependency installation, build, migration, server startup, formatter, or automatic fix was performed. Production builds were deliberately not run because they write generated files. Requests were made only to already-running local services.

## Practical findings

### 1. Next.js installation and configuration

Correct:
- Next, React and React DOM are installed, with matching React/React DOM versions.
- `dev`, `build`, `start`, and `lint` scripts exist.
- `next.config.ts` is typed with `NextConfig`.
- Installed Node 24.18.0 satisfies Next's declared minimum of Node 20.9.0.
- The installed Next documentation explicitly supports the paired `cacheComponents: true` and `partialPrefetching: true` settings. They are not invalid configuration.

Change or decide:
- Align `eslint-config-next` with Next 16.4.0 and update the lockfile through npm.
- Retain Cache Components unless there is a specific reason to opt out. Specify how dynamic health data is rendered without accidentally making it stale, using this installed version's streaming/Suspense conventions.
- `experimental.agentFeedback` is optional development tooling, not application functionality. Remove or disable it later if its feedback workflow is unwanted; it is not a production blocker.
- Document supported Node and package-manager versions and deployment requirements. Cache Components requires a Node runtime.
- A production build and `next start` smoke test are still required before claiming deployment readiness.

### 2. TypeScript and import alias

Correct:
- `strict`, `noEmit`, `isolatedModules`, bundler module resolution, Next plugin, and generated-route type includes are configured.
- Current code type-checks.
- `@/*` maps to `./*`, which is correct for the actual root-level source layout.
- The root layout's generated `LayoutProps<"/">` type resolves in the current setup.

Change or decide:
- Add an explicit type-check script later and run it in CI after appropriate Next type generation.
- Do not hand-edit `next-env.d.ts`.
- No migration to `src` is required. Prefer `lib/api/client.ts`, imported as `@/lib/api/client`, for the current layout.
- If `src` is intentionally adopted later, coordinate source moves and alias mapping together. The currently reported `src/lib/api/client.ts` does not exist.
- `allowJs` and `skipLibCheck` are standard scaffold choices, not defects requiring removal.

### 3. ESLint

The flat-config shape in `eslint.config.mjs` is consistent with current Next documentation, but the installed Next 14 config package is not.

Fix the dependency mismatch rather than adding `.js` to legacy imports as a workaround. After aligning versions, rerun linting and address only real violations. Next builds do not replace a separate lint gate.

### 4. Tailwind CSS

Correct:
- Tailwind v4 is installed.
- `app/globals.css` imports `tailwindcss` and defines theme values with `@theme inline`.
- The root layout imports global CSS.
- `next.config.ts` wires the installed `@tailwindcss/turbopack` loader.
- Existing development CSS demonstrates utility generation.

Consider:
- A missing `tailwind.config.ts` is not itself a problem with Tailwind v4.
- There is no PostCSS config or `@tailwindcss/postcss` package because this project uses a Turbopack-specific path. Do not describe Tailwind as missing or add a duplicate processing pipeline.
- The bundled Next CSS guide recommends the portable PostCSS integration. Keep the working Turbopack path for now; adopt PostCSS only if deployment or a deliberate Webpack fallback requires it, replacing rather than duplicating the current loader.
- Validate styles in a production build before release.

### 5. App Router and UI readiness

Correct:
- Root-level `app/layout.tsx`, `app/page.tsx`, global stylesheet, and favicon form a valid App Router structure.
- The default page is a Server Component; no client directive is needed just to display configuration.
- Next font and image components are in use.

Missing:
- The page remains mostly scaffold content and displays the API URL without requesting an endpoint.
- Metadata still says "Create Next App".
- No API loading/error experience exists. Add appropriate Suspense/loading and error handling with the first integration, not empty convention files merely for completeness.
- No automated frontend tests or CI configuration were found in the inspected project.

### 6. Environment and version control

Correct:
- `.env.local` defines `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api`.
- Frontend `.gitignore` matches `.env*`; Git confirms `.env.local` is ignored and it is not tracked.
- Dependencies and generated Next output are ignored.

Missing or risky:
- `NEXT_PUBLIC_` means public, build-time-inlined browser configuration. Never put secrets in it, and changing it after building does not reconfigure an already-built browser bundle.
- Loopback is development-only. In a deployed browser it points at the user's own machine; in a hosted Next server it points at that server/container, not a separately hosted Django service.
- Add a non-secret `.env.example` later and explicitly allow it in `.gitignore`, because the current `.env*` rule would ignore it.
- The only Git repository found is `frontend/.git`; root and backend are not part of that repository. Backend changes currently lack the frontend's version-control coverage.
- Before a monorepo or separate backend repository is created, define ignores for backend `.env`, `.venv`, Python caches, and local database artifacts. Frontend ignore rules do not protect sibling backend files.

### 7. API client

No API client was found in the actual frontend, including the claimed `src/lib/api/client.ts`.

The later implementation should create a small server-only fetch helper using the existing root layout. Requirements:
- Validate required backend configuration and construct `/api/health/` without losing the `/api` prefix.
- Preserve Django's trailing-slash convention instead of relying on redirects.
- Return a typed health response and validate its minimal runtime shape.
- Surface non-2xx, network, timeout, malformed JSON, and invalid-response errors explicitly.
- Support cancellation or a bounded timeout.
- Keep the first helper narrowly scoped to the health GET; only add generic request-body or no-content handling when endpoints actually require it.
- Never return a success-shaped fallback when the backend is unavailable.
- Do not cache operational health as persistent successful content.
- Do not add credentials or authorization assumptions before authentication is specified.

### 8. Frontend/backend communication

Django routing is correct: `config/urls.py` mounts `core.urls` at `/api/`, and `core/urls.py` defines `/api/health/` and `/api/system-info/`.

Connectivity is partially confirmed: both services respond, and health returns valid JSON. End-to-end frontend communication is not implemented.

No CORS dependency, middleware, or origin policy is configured, and the live response lacks an allow-origin header. A browser fetch from port 3000 to port 8000 cannot read this response. Different ports remain different origins even if both hosts are localhost.

Recommendation:
- First milestone: fetch health from a Next Server Component using a server-only `API_URL`; browser CORS is not involved.
- Later browser mutations or queries: choose either narrowly scoped same-origin Next Route Handlers or explicit direct-browser Django CORS based on hosting and auth requirements.
- If using cookies, specify CSRF token handling, credentials, secure cookies, trusted origins, and logout behavior. CORS is not authentication and does not replace CSRF protection.

### 9. Backend production blockers

`config/settings.py` remains a development configuration:
- `DEBUG = True`.
- A hardcoded development `SECRET_KEY`.
- Empty `ALLOWED_HOSTS`.
- Missing deployment-specific HTTPS/proxy and secure-cookie configuration.
- Console email backend, flagged as an error by `check --deploy`.
- Database credentials are environment-driven, which is good, but database connectivity and migration state were not validated.

The system-info endpoint has no explicit permission restriction and no global DRF permission policy is configured. It exposes host/runtime/resource details under DRF defaults. Remove it from public production routing or protect it with an appropriate administrative permission; do not expose it as the public frontend health check.

The health endpoint proves the API process responds, not that PostgreSQL is ready. Define separate readiness behavior only if deployment requires it.

Production settings must be driven by the eventual hosting model. Do not blindly enable HSTS or trust arbitrary proxy headers before HTTPS and proxy ownership are established.

### 10. Unnecessary changes to avoid

- Do not recreate Next.js or force a `src` migration.
- Do not add legacy Tailwind configuration merely because an older tutorial uses it.
- Do not install CORS middleware if all required requests are server-to-server.
- Do not build an unrestricted generic proxy.
- Do not select JWT, session auth, a state library, a UI framework, or a large test stack before requirements justify them.
- Do not remove valid Next 16.4 caching options based on documentation for older versions.

## Recommended SDD workflow

Use lightweight, repository-owned specs rather than introducing a tool first:

1. Define a short project constitution: strict TypeScript, DRF-owned business rules, explicit errors, no secrets in public env, deliberate caching/auth choices, and tests tied to acceptance criteria.
2. Write a bounded feature spec describing user-visible behavior, scope, non-goals, API contract, and acceptance scenarios.
3. Resolve ambiguities before implementation; record hosting/auth decisions as decisions, not assumptions.
4. Write the technical plan with affected files and contract details.
5. Break the plan into small dependency-aware tasks.
6. Implement one vertical slice, then verify it against the spec and review its diff.
7. Update the spec when behavior changes; do not treat an AI-generated plan as a substitute for the contract.

Proposed first spec: `frontend-api-health`.

Acceptance scenarios:
- Healthy DRF endpoint shows a clear healthy state using the actual response, not the environment variable string.
- Stopped/unreachable backend shows an actionable unavailable state without breaking the whole page.
- Non-2xx and malformed responses are distinguishable from success.
- Health data is not silently served stale.
- Required URL configuration fails clearly when absent.
- Server-only configuration is not bundled into client code.
- Type checking, linting, backend endpoint checks, and a production build pass.

In a later approved implementation, suggested artifacts are `specs\constitution.md`, `specs\frontend-api-health\spec.md`, `plan.md`, and `tasks.md` within that feature folder. Their repository location depends on the version-control decision. No such project files are created by this review.

An SDD toolkit is optional. Start with the workflow above; choose a toolkit only if you need standardized commands and templates. Do not confuse Next's `AGENTS.md` with feature specs or acceptance criteria.

## Implementation todos

Completed todos: `decide-repository-boundary`, `restore-frontend-tooling`, `define-environment-contract`, and `implement-health-slice`. The user approved executing the local integration without first creating SDD artifacts, then approved the root monorepo migration. All other todos remain pending. The prerequisite table below preserves the original planning sequence; approval superseded the initial spec/repository prerequisites for the local milestone.

| ID | Todo | Prerequisites | Expected outcome |
| --- | --- | --- | --- |
| define-health-spec | Defining the first SDD contract | None | Constitution and health feature spec with approved behavior, errors, caching, and non-goals |
| decide-repository-boundary | Defining version-control coverage | None | Deliberate monorepo or separate-repository decision with safe backend ignore rules |
| restore-frontend-tooling | Restoring lint and type-check gates | define-health-spec | Align Next ESLint config, update npm lockfile, add repeatable validation scripts, preserve valid existing Next/Tailwind configuration |
| define-environment-contract | Defining development and production URLs | define-health-spec, decide-repository-boundary | Server-only URL contract and non-secret env example with correct ignore exception |
| implement-health-slice | Implementing the first API connection | restore-frontend-tooling, define-environment-contract | Root-level server-only API helper and health UI with explicit timeout/errors and appropriate dynamic rendering |
| define-deployment-auth | Defining deployment and authentication architecture | define-health-spec | Hosting, domains, browser transport, auth and CSRF decisions recorded before related implementation |
| harden-backend-settings | Hardening deployment configuration | define-deployment-auth, decide-repository-boundary | Environment-driven secret/debug/hosts, appropriate TLS/cookies/email, restricted system-info endpoint, documented database/static handling |
| verify-integration-release | Verifying the first production-ready slice | implement-health-slice, harden-backend-settings | Contract-aligned tests, real healthy/unavailable UI checks, clean lint/type/build checks, deploy checks under production settings, CI gates and project-specific README |

## Validation strategy for future implementation

Use the smallest relevant checks first, then a production smoke test:
- Frontend lint and type checking, with Next type generation where needed.
- DRF health endpoint contract tests; test system-info access policy if retained.
- API helper tests for valid success, non-2xx, timeout/unreachable, invalid JSON/shape, and absent configuration.
- A browser-level smoke scenario for rendered healthy and unavailable states.
- `npm run build` and `npm run start` under intended environment values; confirm Tailwind output and fonts can build in the deployment environment.
- Django `check --deploy` with actual production settings, plus database/migration verification.
- CI should run lint separately from Next build and avoid requiring an operational backend during prerendering unless explicitly part of the contract.

## Remaining decisions

Hosting and authentication are intentionally unresolved. The server-first recommendation is for the initial health slice, not a permanent decision to proxy every request. Product features, authentication implementation, and deployment-provider-specific files are outside this first integration scope unless separately specified.
