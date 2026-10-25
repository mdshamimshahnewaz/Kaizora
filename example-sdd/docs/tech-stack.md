# Timely V4 — Tech Stack

> **Status:** PROPOSED (descriptive document). These are **facts about the current environment**, not approved version requirements. Approved supported versions are **OPEN** (`docs/decisions.md` D-29). The Constitution §3 lists the same facts; it stays as is until amended (D-8).
> **Sources:** `backend/requirements.txt`, `frontend/package.json`, `backend/config/settings.py` and `frontend/README.md`. Python, Node and PostgreSQL versions are as recorded in Constitution §3 (2026-10-09) and cannot be derived from the manifests.

## 1. Foundation (CONFIRMED, Constitution §3)
Django and DRF backend, Next.js frontend, PostgreSQL. Windows development with local PostgreSQL. No Docker or WSL.

## 2. Backend
| Item | Version / state |
|---|---|
| Python | 3.14.5 (Constitution §3) |
| Django | 6.1.2 |
| Django REST Framework | 3.18.3 |
| Psycopg | 3.3.6 (`psycopg`, `psycopg-binary`) |
| django-environ | 0.14.0 |
| PostgreSQL server | 18.4 (Constitution §3) |

- Layout: `backend/config/` (settings, root URLs), `backend/core/` (health and system-info endpoints), `backend/accounts/` (authentication: Entra adapter, identity, roles, sessions, audit; spec 002), `backend/about/` (About content, application identity, Django admin and read endpoints; spec 003), `backend/attendance/` (UNIS attendance sync: clean-architecture module, `public.py` interface, Celery tasks, partitioned punch table; spec 004). The wider module structure is **OPEN** (D-22).
- Settings read the environment through django-environ from `backend/.env`. Variables: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `SECRET_KEY` (required), `DEBUG` (default False), `ALLOWED_HOSTS`, `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_TENANT`, `MICROSOFT_REDIRECT_URI`, `AUTH_SESSION_IDLE_SECONDS`, `AUTH_SESSION_ABSOLUTE_SECONDS`. `backend/.env.example` lists the names without values.
- `TIME_ZONE = 'UTC'`, `USE_TZ = True`.
- Known foundation gaps are listed in `docs/architecture.md` §6.

### Authentication packages (spec 002)
`requests`, `PyJWT` and `cryptography` are used by `accounts/adapters/entra.py` (owner-approved for this use, 2026-10-11). `django-allauth`, `djangorestframework_simplejwt` and `oauthlib` were not used and were removed from `backend/requirements.txt` (D-18 outcome, spec 002 OQ-7).

### Attendance sync packages (spec 004)
`celery` 5.6.3, `django-celery-beat` 2.9.0, `redis` 6.4.0 (client; kombu supports `redis<6.5`) and `mssql-python` 1.16.0 (UNIS MSSQL driver) are owner-approved for `specs/004-attendance-sync` (D-59). Their dependencies are pinned in `backend/requirements.txt`. `django-celery-beat` is installed separately because it declares `Django<6.1` (D-62):
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -r requirements-beat.txt
```
Environment variables (names only, values in `backend/.env`): `REDIS_URL`, `UNIS_OFFICES`, `UNIS_<OFFICE>_HOST|PORT|DATABASE|USER|PASSWORD` for MBD, MHK and RAOWA (read-only logins), `UNIS_TRUST_SERVER_CERTIFICATE`, `UNIS_CONNECT_TIMEOUT_SECONDS`, `UNIS_QUERY_TIMEOUT_SECONDS`, `UNIS_FETCH_CHUNK_ROWS`, `ATTENDANCE_BACKFILL_PAUSE_SECONDS`, `ATTENDANCE_BACKFILL_START_DATE`.
Infrastructure: a Redis server (native install, no Docker/WSL, D-59). Production hosting of Redis, workers and beat is OPEN.

### Installed but not approved and not used
Present in `backend/requirements.txt`. Recorded only.

| Package | Version |
|---|---|
| django-filter | 26.2 |
| psutil | 7.2.2 (used by `system-info`) |
| Markdown | 3.11 |

The remaining entries in `requirements.txt` are transitive or support libraries (asgiref, certifi, cffi, charset-normalizer, idna, pycparser, sqlparse, tzdata, urllib3).

## 3. Frontend
| Item | Version / state |
|---|---|
| Node.js | 24.18.0 (Constitution §3); use Node 24 LTS |
| Next.js | 16.4.0 (App Router) |
| React / React DOM | 19.3.0 |
| TypeScript | 5.9.3 (`^5` in `package.json`) |
| Tailwind CSS | v4 via `@tailwindcss/turbopack` |
| ESLint | 9, with `eslint-config-next` 16.4.0 |
| server-only | 0.0.1 |
| @tabler/icons-react | 3.49.0 (icons; PROPOSED, owner-approved for `specs/001-ui-foundation`) |
| @radix-ui/react-dialog | 1.2.0 (dialog, drawer; same approval) |
| @radix-ui/react-dropdown-menu | 2.1.25 (same approval) |
| @radix-ui/react-tooltip | 1.3.0 (same approval) |
| @radix-ui/react-tabs | 1.1.22 (same approval) |

- UI rules (tokens, shared components, navigation, theme): `docs/frontend-ui-rules.md` (PROPOSED).
- Shared API client: `frontend/lib/api/client.ts` (server-only; reads `API_URL`).
- `API_URL` is a **server-only** base URL (example in `frontend/.env.example`). Never put secrets in `NEXT_PUBLIC_*`.
- `APP_ORIGIN` is a server-only, non-secret origin of the frontend (used by the auth Route Handlers for redirects, the logout origin check and the Secure cookie flag).
- Next.js 16 has breaking changes; read `frontend/node_modules/next/dist/docs/` before writing Next code (`frontend/AGENTS.md`).
- Setup details: `frontend/README.md`.

## 4. Commands (PowerShell)
Frontend, from `frontend\`:
```powershell
npm ci
npm run dev
npm run lint
npm run typecheck
npm test
npm run build
```

Backend, from `backend\`:
```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test core
.\.venv\Scripts\python.exe manage.py test about
.\.venv\Scripts\python.exe manage.py test accounts
.\.venv\Scripts\python.exe manage.py test attendance
```

Attendance sync (spec 004), from `backend\`, with Redis running. Day to day you manage it in **Django Admin → Attendance**. First-time setup (Beat schedule, forward-sync start point, monthly partitions) is **Attendance → Attendance setup** (needs the `manage_schedule` permission); after `migrate` and `createsuperuser` open that page and press the three steps. The terminal is only needed to migrate and to start the background processes. The commands below do the same as that page and stay available:
```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py setup_attendance_schedule     # beat entries (sync 5 min, heartbeat 1 min, partitions and housekeeping daily); keeps what you changed in Admin
.\.venv\Scripts\python.exe manage.py init_forward_sync             # forward sync starts from today 00:00 (Asia/Dhaka)

# One command starts and supervises the sync worker, the backfill worker and Beat (restarts a crashed process, logs to backend\logs\attendance\):
.\.venv\Scripts\python.exe manage.py run_attendance_services
.\.venv\Scripts\python.exe manage.py run_attendance_services --status
.\.venv\Scripts\python.exe manage.py run_attendance_services --stop

# Windows: start it automatically when you sign in (no administrator rights). From the repository root:
.\scripts\windows\attendance-service.ps1 install      # also: start | stop | status | uninstall
```
Windows has no Docker/WSL, so each worker uses `--pool=solo` and one queue (`attendance_sync`, `attendance_backfill`); a long backfill never blocks the 5-minute sync. Redis: `REDIS_URL` (use `127.0.0.1`, not `localhost`, on Windows: `localhost` adds about two seconds to every new connection) and optionally `REDIS_SERVER_PATH` so the supervisor starts a local Redis itself.
The auto-start task runs while you are signed in. For always-on servers see `deploy/windows-service.md` (Windows service option, needs separate approval) and `deploy/systemd/` (Linux units, reference for production; templates only).

History is requested in **Backfill jobs** (one office and range per job; over 31 days needs the confirmation and the large-backfill permission; nothing starts a backfill by itself). The command line still works for operators:
```powershell
.\.venv\Scripts\python.exe manage.py backfill_attendance --office MBD --from 2019-01-01 --enqueue
.\.venv\Scripts\python.exe manage.py ensure_partitions
```

Admin permissions (all in the `attendance` app; superusers hold them all; assign them to groups as the owner decides): `trigger_sync`, `retry_runs`, `manage_backfill`, `manage_large_backfill`, `view_health`, `manage_schedule`, plus Django's standard view permissions for the read-only lists. The generic django-celery-beat admin pages are superuser-only.
Optional settings (defaults in `backend/.env.example`): `ATTENDANCE_BACKFILL_MAX_DAYS`, `ATTENDANCE_LARGE_BACKFILL_DAYS`, `ATTENDANCE_RETENTION_*_DAYS`, `ATTENDANCE_QUEUED_EXPIRY_MINUTES`, `ATTENDANCE_HEALTH_TIMEOUT_SECONDS`, `ATTENDANCE_LOG_DIR`, `REDIS_SERVER_PATH`.

Manual process commands (what the supervisor runs, for debugging):
```powershell
.\.venv\Scripts\python.exe -m celery -A config.celery worker --pool=solo -Q attendance_sync -n sync@%h -l info
.\.venv\Scripts\python.exe -m celery -A config.celery worker --pool=solo -Q attendance_backfill -n backfill@%h -l info
.\.venv\Scripts\python.exe -m celery -A config.celery beat -l info
```

## 5. Not yet decided (OPEN / DEFERRED)
Approved supported versions, production hosting and deployment, background jobs, real-time, contract-generation and lint-enforcement tooling. Authentication is decided in D-55. See `docs/decisions.md`.
