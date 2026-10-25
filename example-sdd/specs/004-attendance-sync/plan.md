# Technical Plan — Attendance Sync

> **Purpose:** HOW the approved `spec.md` will be implemented. Every decision traces to a spec item.
> **Location:** `specs/004-attendance-sync/plan.md`. **Rules:** `docs/constitution.md` (v1.1), `docs/architecture.md`, `docs/api-conventions.md`.
> Every decision is marked CONFIRMED, PROPOSED, OPEN or DEFERRED. **Nothing in this plan is CONFIRMED yet.**
> Written from the approved spec (2026-10-14). Existing code was read only; the only things run were read-only package checks (see §8).

## 1. Linked Spec
Source: `specs/004-attendance-sync/spec.md` · Covers: US-1 to US-6, AC-1.1 to AC-6.2, AC-D.1 to AC-D.3.

## 2. Architecture Overview
- **One new Django app `backend/attendance/`**, a clean-architecture module with only the layers that earn their place (AR-6). **[PROPOSED; module structure is OPEN D-22, this plan proposes it]**

```
backend/attendance/
  public.py            THE ONLY file other modules may import: DTOs + list_punches, get_sync_status, get_reconciliation
  domain/              Punch, Office, SyncWindow (value objects, pure Python, no Django, no UNIS words)
  application/         use cases: BackfillOffice, ForwardSync, ReconcileDay, QueryPunches, GetSyncStatus
                       ports.py: PunchSource, PunchRepository, ProgressRepository, Clock, OfficeLock
  infrastructure/
    unis/              MSSQL adapter implementing PunchSource (the ONLY place with tEnter, L_UID, ...)
    persistence/       PostgreSQL repositories (raw SQL for punches, ORM for small tables), partition helper
    tasks.py           Celery tasks (thin: build use case, call it, record result)
  models.py            small tables only (progress, runs, reconciliation); NO punch ORM model
  management/commands/ backfill_attendance, init_forward_sync, ensure_partitions, setup_attendance_schedule
  admin.py             read-only admin for runs, cursors, reconciliation
  tests/
backend/config/celery.py   Celery app (settings namespace CELERY_)
```
- **Dependency direction:** `infrastructure → application → domain`. `application` depends only on the ports. UNIS vocabulary, the MSSQL driver and Celery never appear in `domain` or `application` (P4, AC-6.1).
- **Microservice path:** the use cases, ports and domain move unchanged into a separate service. Only `public.py` is replaced by an HTTP/gRPC client with the same function signatures and DTOs; the PostgreSQL tables move with the module. No other module ever reads the tables, so nothing else changes (AR-5, AR-8, US-4).
- **Runtime:** Celery worker(s) + Celery beat (django-celery-beat, database schedule) + Redis broker. Frontend: none. BFF: none.

## 3. Data Model and Ownership
All tables belong to module `attendance`. No foreign keys to or from any other module; `eid` is an opaque string (D-31 stays OPEN, flagged).

```
Table: attendance_punch      (raw SQL migration, PARTITIONED BY RANGE (date), one partition per month)
  office      varchar(16)   NOT NULL      -- MBD | MHK | RAOWA (AC-D.3)
  eid         varchar(64)   NOT NULL      -- UNIS Id (AC-D.1)
  date        date          NOT NULL      -- local Asia/Dhaka (AC-D.2)
  time        time          NOT NULL      -- local Asia/Dhaka, to the second
  terminal    varchar(255)  NOT NULL
  rfid        varchar(64)   NULL          -- text, leading zeros kept
  geolocation text          NULL          -- empty for now
  created_at  timestamptz   NOT NULL DEFAULT now()
  updated_at  timestamptz   NOT NULL DEFAULT now()
  UNIQUE (office, eid, date, time, terminal)    -- includes the partition key (required by PostgreSQL); AC-3.1
  INDEX  (eid, date, time)                      -- reads by employee and date range
  DEFAULT partition attendance_punch_default    -- safety net, should stay empty (monitored)
Partitions: attendance_punch_YYYY_MM, 2019-01 up to the current month + 3 future months.
No surrogate id: nothing needs one, and a partitioned primary key must contain the partition key anyway.

Table: attendance_sync_cursor   (ORM)  office (unique), last_date, last_time, last_success_at, last_error_at, last_error_kind, updated_at
Table: attendance_backfill_day  (ORM)  office, date, status (pending|done|failed), unis_count, inserted_count, finished_at; unique (office, date)
Table: attendance_sync_run      (ORM)  kind (forward|backfill|reconcile), office, date_from, date_to, started_at, finished_at,
                                       read_count, inserted_count, result (ok|failed), error_kind     (AC-5.1; no personal data)
Table: attendance_reconciliation(ORM)  office, date, unis_count, local_count, is_mismatch, checked_at; unique (office, date)   (AC-5.2)
```
- **Why raw SQL for punches:** Django's ORM cannot declare partitioned tables, and bulk `ON CONFLICT DO NOTHING` plus `COPY` is needed at 50M+ rows. The repository owns that SQL; nothing else touches the table. Small tables use the ORM and normal migrations. No new dependency.
- **Monthly partitioning (owner: "primarily monthly") [PROPOSED]:** created by the migration for 2019-01 onward and kept ahead by `ensure_partitions` (run from Celery beat daily). Old partitions can be detached for retention later (OQ-2, DEFERRED).
- **Volume estimate:** ~50M rows / 80 months ≈ 0.6M rows per partition; the unique index and the `(eid, date, time)` index are the only indexes.
- **Transaction boundary (AR-13):** one transaction per (office, day batch) = punch insert + progress/cursor update. Owner: `attendance`.
- **Migrations:** `0001` ORM tables; `0002` RunSQL partitioned table, partitions, default partition, indexes (reversible: drop table).

## 4. Contracts
### 4.1 HTTP API
**None.** No endpoint, no frontend work (spec §9). A later feature adds an HTTP layer on top of `public.py` (AR-14).

### 4.2 Internal interface — `attendance/public.py` (the only importable file)
```
@dataclass(frozen=True) PunchDTO:  office, eid, date, time, terminal, rfid, geolocation
@dataclass(frozen=True) PunchPage: items: tuple[PunchDTO, ...], next_cursor: str | None
@dataclass(frozen=True) OfficeStatusDTO: office, last_success_at, last_error_at, last_error_kind, data_as_of (date, time)
@dataclass(frozen=True) ReconciliationDTO: office, date, unis_count, local_count, is_mismatch, checked_at

list_punches(*, eids: Sequence[str] | None, office: str | None, date_from: date, date_to: date,
             limit: int = 500, cursor: str | None = None) -> PunchPage
get_sync_status() -> tuple[OfficeStatusDTO, ...]
get_reconciliation(*, office: str | None, date_from: date, date_to: date) -> tuple[ReconciliationDTO, ...]
```
- **Keyset pagination**, not offset (api-conventions §3: large append-only data uses cursor pagination). Order is `(date, time, office, eid, terminal)`; the cursor is an opaque string of the last tuple. Maximum `limit` 1000 and the date range maximum (e.g. 31 days when `eids` is empty) are validated; limits are PROPOSED (D-24 page sizes OPEN, flagged).
- `date_from`/`date_to` are required; there is no unbounded read.
- Errors: invalid arguments raise `ValueError` subclasses defined in `public.py`; no ORM or driver exception leaves the module.
- **Boundary rule:** `attendance` imports no other app; no other app imports anything under `attendance` except `attendance.public`. Enforced by an automated test (§10, AC-4.3). No new tooling.

### 4.3 Operator commands (AC-1.3)
- `backfill_attendance [--office MBD] [--from 2019-01-01] [--to YYYY-MM-DD] [--enqueue]` (default offices: all, `--to` default: today). Without `--enqueue` it runs inline for the dev machine; with it, it sends one chained task per office to the `attendance_backfill` queue.
- `init_forward_sync [--office X] [--from-date YYYY-MM-DD]` sets the initial cursor (default: start of today, Asia/Dhaka) (OQ-4).
- `ensure_partitions [--months-ahead 3]`, `setup_attendance_schedule` (idempotent: creates the 5-minute and daily beat entries).

## 5. Sync Design
**Forward sync (AC-2.x), Celery task `forward_sync_all`, queue `attendance_sync`, every 5 minutes.**
1. For each configured office, sequentially: try the office lock (below); if taken, skip and record "skipped, busy" (AC-2.3).
2. Read the cursor `(last_date, last_time)`. The window is: that day from `last_time` (inclusive, so a second with several punches is never cut) to the end of the day, then every following day up to today (Asia/Dhaka "now").
3. Read from UNIS in chunks, map to `Punch`, write via temp table + `INSERT ... ON CONFLICT DO NOTHING` (idempotent, AC-3.1), then advance the cursor to the max `(date, time)` seen, all in one transaction per day (AC-3.2).
4. Record a `SyncRun`. Any failure for one office is caught, recorded with `error_kind` only, and the loop continues with the next office (AC-2.2). The cursor stays where it was, so the next run retries the same window.
5. After the day's insert, reconcile today (count query, below).
- Late or edited rows are out of scope, so there is no re-read window beyond the inclusive cursor second.

**Backfill (AC-1.x), task `backfill_office` chain per office, queue `attendance_backfill`.**
- Days are processed oldest to newest. A day with `BackfillDay.status = done` is skipped (AC-1.2). Each day = one transaction, then `ReconcileDay`. A failed day is marked `failed`, recorded, and the chain stops for that office; rerunning resumes from the first not-done day.
- **Throttle (OQ-4, PROPOSED):** one day at a time per office, 3 offices in parallel at most, and a configurable pause `ATTENDANCE_BACKFILL_PAUSE_SECONDS` (default 1) between days. Roughly 3 offices x 7 years = ~7,700 office-days, so a full backfill is long but bounded; the owner may raise parallelism after watching UNIS load.
- Backfill and forward sync may overlap in dates (both are idempotent), but never run at the same moment for the same office (lock).

**Office lock (AC-2.3, AC-3.3):** a PostgreSQL session advisory lock per office (`pg_try_advisory_lock(hash(office))`), held for one office-day (backfill) or one office run (forward), released in `finally`. PostgreSQL is already required, so Redis is not used for locking and a lost Redis cannot cause double processing. **[PROPOSED]**

**Reconciliation (AC-5.2):** `ReconcileDay` runs `SELECT COUNT(*)` for the office/day on UNIS and counts local rows by (office, date), then upserts the row, `is_mismatch = local < unis`. Backfill reconciles each finished day; forward sync reconciles today after each run and yesterday once after midnight. A mismatch is stored, logged as a warning with counts only, and never auto-fixed.

**Time:** UNIS date/time are stored as read (Asia/Dhaka, AC-D.2). "Today" and "now" come from `zoneinfo.ZoneInfo("Asia/Dhaka")` through an injected `Clock`. Django `TIME_ZONE` stays UTC for its own timestamps (`created_at`). **[Owner-approved exception to api-conventions §2, to be recorded as a decision.]**

## 6. External Systems and Adapters
**UNIS (read-only), behind `PunchSource` (P4).** Port methods: `read_punches(office, day, from_time=None) -> Iterator[Punch]` and `count_punches(office, day) -> int`.
- Adapter SQL (parameterised, never string-built from data; the legacy `$exclude` clause is replaced by the database unique key):
  `SELECT e.L_UID, e.C_Date, e.C_Time, t.C_Name, e.C_Card FROM <db>.dbo.tEnter e INNER JOIN <db>.dbo.tTerminal t ON t.L_ID = e.L_TID WHERE e.C_Date = ? AND e.C_Time >= ? ORDER BY e.C_Time`
  The database name cannot be a parameter, so it comes only from configuration and must match `^[A-Za-z0-9_]+$`.
- Mapping: `L_UID→eid`, `C_Date ('yyyymmdd')→date`, `C_Time ('HHMMSS')→time`, `C_Name→terminal`, `C_Card→rfid` (kept as text, empty → NULL). A malformed row is skipped, counted, and recorded in the run's `error_kind` count; it never aborts the day silently.
- Access: read-only SQL login (owner has credentials), `ApplicationIntent=ReadOnly`, connect timeout 10 s, query timeout 60 s, fetch in chunks of 5,000. The adapter never writes to UNIS.
- **Configuration (environment only; AC-6.2):** `UNIS_OFFICES=MBD,MHK,RAOWA` and, per office, `UNIS_<OFFICE>_HOST`, `_PORT`, `_DATABASE` (RAOWA is `UNISNew`, the others `UNIS`), `_USER`, `_PASSWORD`, plus `UNIS_TRUST_SERVER_CERTIFICATE`. `backend/.env.example` lists names without values. Credentials are never logged, never in exceptions (the adapter wraps driver errors into `UnisUnavailable` / `UnisQueryError` with a kind only).
- **Failure behaviour:** UNIS down or slow → the run is recorded as failed, existing data is kept, the cursor does not move, other offices continue, status shows the last error and "data as of".
- **Driver choice:** see §8. The adapter is the only module that imports it, so it can be swapped without touching anything else.

## 7. Security
- No HTTP surface, so no new authentication surface. Access to data is only through `public.py` inside the process; end-user permissions are deferred to the API feature (OQ-3).
- Secrets only from the environment; none in logs, errors, run records or the repository (P5). RFID numbers and EIDs are never logged; logs and `SyncRun` hold office, dates, counts and an error kind.
- UNIS login must be read-only; a deployment check (`manage.py check` extension or a startup test) confirms the adapter issues only `SELECT`.
- Celery: JSON serializer only (no pickle), broker on localhost/private network, Redis password via environment when it is not local. Task arguments contain only office codes and dates.
- Admin: read-only admin pages for `SyncRun`, `SyncCursor`, `BackfillDay`, `Reconciliation` (no add/change/delete; no punch admin, to avoid loading 50M rows). **[PROPOSED]**
- Audit: sync runs (AC-5.1). Specific security audit events remain OPEN (D-30).

## 8. Tech Choices, New Dependencies and Infrastructure (P7: all need explicit owner approval)
| Decision | Options considered | Chosen | Status | Why |
|---|---|---|---|---|
| Scheduler / worker | management command + OS scheduler; Procrastinate; Celery + beat | **Celery + django-celery-beat** (owner choice 2026-10-14) | PROPOSED (needs approval, D-40) | Owner decision. Beat schedule lives in the database. |
| Broker | Redis; RabbitMQ | **Redis** (owner choice) | PROPOSED (needs approval) | Owner decision. |
| MSSQL driver | `mssql-python`; `pyodbc`; `pymssql` | **`mssql-python`**, fallback `pyodbc` | PROPOSED (needs approval) | Microsoft's official GA driver; `pip install` only on Windows. Verified on PyPI: `mssql_python-1.16.0-cp314-cp314-win_amd64.whl` exists. `pyodbc-5.3.0-cp314-cp314-win_amd64.whl` also exists; on this dev machine "ODBC Driver 18 for SQL Server" is installed, so either works here. `pymssql` rejected (not checked for 3.14, weaker maintenance). The port keeps this choice reversible. |
| Punch storage | one big table; monthly partitions | **Monthly partitions** by `date` | PROPOSED | 50M+ rows; owner: "primarily monthly". |
| Dedup | NOT-IN query like legacy; DB unique key | DB unique key + `ON CONFLICT DO NOTHING` | PROPOSED | Idempotent, no giant exclude clause. |
| Office lock | Redis lock; PostgreSQL advisory lock | PostgreSQL advisory lock | PROPOSED | Survives Redis loss, no extra dependency. |
| Boundary enforcement | `import-linter`; own AST test | own AST test | PROPOSED | No new tool (D-26). |

**New dependencies (pinned in `backend/requirements.txt` after approval):**
| Package | Version checked | Note |
|---|---|---|
| `celery` | 5.6.3 (pure-Python wheel available) | Official Windows support is limited; use `--pool=solo`. Compatibility with Django 6.1 and Python 3.14 is **not yet proven**; the first task verifies it. |
| `django-celery-beat` | 2.9.0 (pure-Python wheel available) | Django 6.1 compatibility **not yet proven**; verified in the first task. Adds its own tables. |
| `redis` (client) | 8.1.0 (pure-Python wheel available) | |
| `mssql-python` | 1.16.0 (cp314 win_amd64 wheel available) | Wheel presence verified; a real connection is **not yet tested** (needs the owner's credentials, a task step). |
Transitive packages (e.g. kombu, billiard, vine, amqp, tzlocal, cron-descriptor, python-crontab) come with them and are listed in the approval record after install.

**New infrastructure:** a **Redis server**. Redis has no official Windows build, and Docker/WSL are forbidden (P7). Options for the Windows dev machine, to be decided by the owner **[OPEN, OQ-P1]**: Memurai (Redis-compatible, native Windows service, free developer edition), or an unofficial Windows Redis build. Redis was **not found** on this machine (checked service and PATH). Production hosting of Redis, workers and beat is OPEN (Constitution §3).
- **Worker layout on Windows:** two worker processes with `--pool=solo` and one queue each (`attendance_sync`, `attendance_backfill`), so a long backfill never blocks the 5-minute sync, plus one `celery beat` process. Production process management (services) is OPEN.

## 9. Traceability Matrix
| Spec item | Plan section | Notes |
|---|---|---|
| US-1 / AC-1.1–1.3 | §4.3, §5 backfill | resumable per office/day; range limits via command |
| US-2 / AC-2.1–2.3 | §5 forward sync, lock | per-office isolation |
| US-3 / AC-3.1–3.3 | §3 unique key, §5 transactions and lock | idempotent upsert |
| US-4 / AC-4.1–4.3 | §4.2, §2 boundary | keyset pagination; AST boundary test |
| US-5 / AC-5.1–5.3 | §3 tables, §5 reconcile, §7 admin | read-only admin + `public` status |
| US-6 / AC-6.1, 6.2 | §6, §7 | adapter isolation; env-only secrets |
| AC-D.1–D.3 | §3, §5 time | legacy columns, local time, office = server |

## 10. Testing Strategy
- **Domain/application (no DB, no UNIS):** use cases with in-memory fakes of the ports: forward window calculation across day boundaries and downtime; cursor advances only on commit; backfill resume skips done days; one-office failure does not stop the others; lock busy → skip; reconciliation mismatch flag.
- **Persistence (real PostgreSQL test DB, migrations applied):** partitioned table exists with the right partitions and default partition; `ON CONFLICT DO NOTHING` idempotency (AC-3.1); terminal in key (same second, two terminals → two rows); rollback leaves nothing (AC-3.2); keyset pagination order and cursor; `ensure_partitions` idempotent; RFID leading zeros kept.
- **UNIS adapter (driver mocked):** row mapping and malformed rows; parameterised query (no data in SQL text); database-name validation; timeouts and driver errors wrapped without credentials; no write statements.
- **Tasks:** Celery eager mode for `forward_sync_all` and the backfill chain; schedule setup idempotent; per-office error isolation.
- **Boundary test (AC-4.3):** scans backend Python files with `ast`: nothing outside `attendance/` imports `attendance` except `attendance.public`, and `attendance` imports no other local app (settings/Django/Celery excepted).
- **Secrets test (AC-6.2):** a failing adapter's exception text and logs contain no password or host.
- **Static checks:** `manage.py check`, `makemigrations --check`, `manage.py test attendance accounts about core`.
- **Manual (reported separately, never counted as Passed until run):** real read-only connection to each UNIS server (counts match the legacy `SystemMonitor`), a one-day backfill and comparison with the Laravel data, Redis + worker + beat running for several 5-minute cycles on Windows, stopping UNIS and Redis mid-run, insert speed and partition sizes on a large test load, memory use with a 5,000-row chunk.

## 11. Risks & Mitigations
- **Celery on Windows is not officially supported** → solo pools, separate queues, smoke test early in task 1; fall back to Procrastinate or a management command behind the same task functions if it proves unstable (owner decision).
- **Celery / django-celery-beat compatibility with Django 6.1 and Python 3.14 unproven** → first task is an isolated install + `manage.py check` + eager-task test before any other work.
- **Redis on Windows without Docker/WSL** → Memurai or a Windows build; decision needed (OQ-P1). Broker loss only delays syncing, never loses data (cursor + idempotency).
- **UNIS has no row id and `C_Date`/`C_Time` types are unknown** (assumed fixed-width text from the samples) → the adapter confirms types in the first real-connection check; if they are numeric or datetime, only the adapter changes.
- **Two real punches with identical (office, eid, date, time, terminal) collapse into one** → accepted by the owner's key choice, same as the legacy behaviour for those fields.
- **UNIS load during backfill** → throttle, 3 parallel at most, off-peak hours configurable.
- **Partition gaps** (a date beyond the last partition) → default partition + daily `ensure_partitions` + a status warning if the default partition is not empty.
- **Large backfill transactions** → one day per transaction (~6,500 rows per office/day estimated), small.
- **Different UNIS DB names per office** → per-office `_DATABASE` setting, validated.
- **Personal data (EID, RFID)** → interface-only access; nothing in logs.

## 12. Constitution Check
| Principle | Compliant? | Notes |
|---|---|---|
| P1 Spec first, gates | Yes | Approved spec; this plan awaits approval. |
| P2 Decisions labelled | Yes | All PROPOSED; open points in §13. |
| P3 Modular monolith | Yes | One module, interface-only access; module structure OPEN (D-22), proposed here. |
| P4 Adapters for external systems | Yes | UNIS only through `PunchSource`, read-only. |
| P5 Security, privacy, audit | Yes, with flags | Secrets from environment, no data in logs, run records; audit events OPEN (D-30). |
| P6 Evidence-based validation | Yes | Strategy §10; manual checks reported separately. |
| P7 Minimal footprint | **Needs approval** | 4 new packages + Redis server. No Docker/WSL. No AI. |
| P8 API-first | Yes | No HTTP API now; `public.py` is the contract the later API will wrap; no frontend or BFF. |

## 13. Open Points for the Owner
- **OQ-P1 (Redis on Windows):** Memurai or another native Redis build for the dev machine? And later production hosting of Redis/worker/beat (OPEN).
- **OQ-P2 (dependencies):** approve `celery`, `django-celery-beat`, `redis`, `mssql-python` (fallback `pyodbc`), and Redis, with the compatibility checks in task 1.
- **OQ-P3 (partitioning, interface, structure):** approve monthly partitioning and raw-SQL punch table; the `attendance` module structure (D-22); keyset-paginated `list_punches` limits (max 1000, 31-day span when no EID filter).
- **OQ-P4 (forward start, OQ-4):** initial forward cursor = start of today (Asia/Dhaka); backfill default range 2019-01-01 to today; backfill throttle 3 offices parallel, 1 s pause per day.
- **OQ-P5 (read-only admin):** approve read-only admin pages for runs, cursors, backfill days and reconciliation.
- **OQ-P6 (decision records):** record the time-zone exception (AC-D.2), D-40 resolved for attendance (Celery + Redis), and D-22 module structure in `docs/decisions.md` after approval.
- **DEFERRED:** retention (OQ-2), read permissions (OQ-3).
- UNIS credentials are supplied by the owner in `backend/.env`; the agent never reads or prints them.

## 13a. Amendment A-1 — Admin-managed operations, health and reliable startup (APPROVED 2026-10-15; implemented)

> Covers spec US-7 to US-13 and AC-7.x to AC-13.x (spec §3a). Approved by the owner on 2026-10-15 together with the proposed defaults OQ-A1 to OQ-A8 and the items in §13a.14. Approval does not authorise implementation (D-6). Sections 2 to 13 stay as approved except where this section says otherwise. `attendance.public` and the module boundary do not change.

### 13a.1 What exists today and what is missing
| Need (spec) | Exists now (verified in the code and the admin registry) | Missing |
|---|---|---|
| Schedule management (US-7) | django-celery-beat's generic admin: periodic tasks and intervals, enable / disable / toggle and a "Run selected tasks" action, `last_run_at` in the list. Two beat entries from `setup_attendance_schedule`. | A page limited to attendance jobs; an **estimated** next run; interval limits; no deleting default jobs; audit of changes; task results (`CELERY_TASK_IGNORE_RESULT=True`, no results table). The generic admin can create any task name and its run action bypasses audit. |
| Sync operations (US-8) | `forward_sync_all` task and inline use cases; read-only admin lists for `SyncRun` and `SyncCursor`; per-office lock. | "Sync now" for chosen offices; duplicate-trigger guard; retry of failed runs; who-triggered and retry link on runs; a task-execution history. |
| Backfill management (US-9) | `backfill_attendance` command (inline or `--enqueue` month chains), `BackfillDay` rows, resumable use case. | A job record, an admin form with validation, overlap guard, progress, resume, cancel, "re-check loaded days" option, large-range confirmation and permission. |
| Reconciliation views (US-10) | Read-only `Reconciliation` and `SyncCursor` lists. | Filters (mismatch only), difference column, per-office summary with last success, open mismatches and links. |
| Operational health (US-11) | Nothing (only `get_sync_status` data). | Broker, worker and scheduler checks; basis labels; heartbeat job; UNIS test connection. |
| Reliable startup (US-12) | Commands documented in `docs/tech-stack.md` that must be typed in separate terminals; Redis started by hand. | A supervisor, Windows auto-start, production service definitions, logs. |
| Security and audit (US-13) | Standard Django admin staff login and model permissions; read-only models; `SyncRun` records. | Dedicated permissions, input validation for operations, audit log, POST-only actions with CSRF (Django default), permission matrix tests. |

### 13a.2 Architecture
- **Stays:** layers `domain/`, `application/`, `infrastructure/`, `public.py`. Admin code is part of `attendance` and may use its own use cases, repositories and tasks. No other module imports it. No new package.
- **Admin package:** `attendance/admin.py` becomes a package `attendance/admin/` with modules `schedule.py`, `sync.py`, `backfill.py`, `reconciliation.py`, `health.py`, `audit.py`; `__init__` registers them. Custom pages use `ModelAdmin.get_urls` and templates under `attendance/templates/admin/attendance/`.
- **Application layer:** new `application/operations.py` with `TriggerSync`, `RetryRun`, `RequestBackfill`, `ResumeBackfill`, `CancelBackfill` use cases (validation, overlap rules, caps, who and when) depending only on ports (`JobRepository`, `TaskPublisher`, `AuditLog`, `Clock`, `OfficeLock`). Admin classes are thin: they call a use case and show its answer.
- **Infrastructure layer:** `infrastructure/publisher.py` (Celery `apply_async(retry=False)`, fail fast when Redis is down), `infrastructure/health.py` (checks), `infrastructure/signals.py` (Celery signal handlers that update `TaskEvent`), `infrastructure/supervisor.py` (process supervisor), housekeeping task.
- **Tasks:** `forward_sync_all` is kept (scheduled). New `forward_sync_offices(offices, triggered_by, event_id)` shares its code; `backfill_office` gains `job_id`; new `attendance.heartbeat` (every minute) and `attendance.housekeeping` (daily: prunes `TaskEvent`, heartbeat evidence and audit rows past their retention, and marks stale queued events expired).
- **Use-case change (small, approved-scope):** `BackfillOffice` gains two optional callbacks, `should_continue()` (cancel check between days) and `on_day(day, inserted)` (progress), both default to no-ops, so the approved behaviour and tests are unchanged.
- **No HTTP API and no frontend change.** Admin URLs live under `/admin/attendance/…`. The BFF register is unaffected.

### 13a.3 Data model additions (all owned by `attendance`; no foreign keys to other modules)
```
BackfillJob      office, date_from, date_to, recheck_loaded_days (bool), state (queued|running|done|failed|cancelled),
                 cancel_requested (bool), requested_by_id (int, no FK), requested_by_name, requested_at, started_at, finished_at,
                 days_total, days_done, rows_inserted, failed_day (date, null), last_error_kind, first_task_id
                 Meta.ordering = -id; progress is also derived from BackfillDay inside the range.
TaskEvent        event_id (uuid, = Celery task id), task_name, queue, state (queued|running|success|failure|expired),
                 queued_at, started_at, finished_at, triggered_by ('scheduled' or a user name), job_id (null),
                 summary (small JSON: counts, error kind; never punch data)
OperationAudit   at, actor_id, actor_name, action (sync_triggered|run_retried|backfill_requested|backfill_resumed|
                 backfill_cancelled|schedule_changed|connection_tested|refused), office, date_from, date_to,
                 job_id, run_id, task_id, outcome (queued|refused|failed|ok), detail (short text, no data)
SyncRun (existing) + triggered_by (text, '' = scheduled), celery_task_id, retry_of (nullable id of the failed run)
Permissions      declared on OperationAudit.Meta.permissions: trigger_sync, retry_runs, manage_backfill,
                 manage_large_backfill, view_health, manage_schedule   (plus Django's standard view permissions)
```
- Migration `0003` adds the tables, the `SyncRun` columns and the permissions. Existing rows keep working (`triggered_by=''`).
- Records hold counts, dates, office codes, statuses, error kinds and the acting user, never EIDs, RFIDs, hosts or secrets.
- Retention (OQ-A3, PROPOSED): `TaskEvent` 30 days, heartbeat events 2 days, `OperationAudit` 365 days, all settings. `SyncRun`, `Reconciliation` and `BackfillJob` are not pruned.

### 13a.4 Admin pages and behaviour
| Page (Django Admin) | Backed by | Behaviour |
|---|---|---|
| **Attendance schedule** | proxy model of django-celery-beat `PeriodicTask`, queryset limited to `attendance.*` tasks | Columns: name, task, queue, interval, enabled, last run, total runs, **estimated** next run (`schedule.remaining_estimate(last_run_at)`, labelled "estimated"). Edit only enabled and interval. Interval limits: forward sync 1 to 60 minutes; heartbeat and partitions fixed. Cannot add, cannot delete default jobs, no free-text task name (AC-7.3). Needs `manage_schedule`. Changes audited. Beat's database scheduler picks changes up without restart. |
| **Task executions** | `TaskEvent` | Read-only list with filters (task, state, date), duration, counts, error kind (AC-7.4). |
| **Sync cursors** | `SyncCursor` | Existing list plus action **"Sync selected offices now"** (needs `trigger_sync`) and **"Test UNIS connection"** (needs `trigger_sync`). |
| **Sync runs** | `SyncRun` | Read-only history with filters by office, kind, result, date; columns triggered by, retry link; action **"Retry selected failed runs"** (needs `retry_runs`). |
| **Backfill jobs** | `BackfillJob` | Add form: office, from, to, "re-check loaded days"; confirmation checkbox shown and required above 31 days (also needs `manage_large_backfill`). List with state, progress bar (done / total days), rows, failed day, error kind. Actions: **Resume** and **Cancel** (need `manage_backfill`). Change view is read-only. |
| **Reconciliation** | `Reconciliation` | Read-only list: difference column, filters (office, date, mismatch only); per-office **summary** page: last success, last error kind, data as of, open mismatch count, links to runs and to a prefilled backfill form (AC-10.x). |
| **Operations health** | unmanaged model (`managed=False`, no table) hosting a custom view | Shows the status table of §13a.6; a "Test connection" button per office (POST); needs `view_health`. |
| **Audit log** | `OperationAudit` | Read-only, filterable. |

- **Actions only publish.** They validate, write an audit row, create or update the `TaskEvent` / `BackfillJob`, publish the task with `apply_async(retry=False)` and return. They never wait for UNIS. If Redis is down the page shows "could not queue (broker unavailable)", the event is not left as queued, and an audit row records `failed`.
- **Duplicate-trigger guard (AC-8.2):** an office is refused when (a) a `TaskEvent` for it is `queued` or `running` and not expired (queued events expire after 15 minutes without starting, so a lost message does not block forever), or (b) its advisory lock is currently held (tried and released at once).
- **Retry (AC-8.3):** allowed only for `SyncRun.result = failed` that is the latest run of that office and kind and where no active run exists. Forward retry = `forward_sync_offices([office])` (continues from the saved cursor). Backfill retry = resume of the job that owns the failed day. Both are idempotent because of the unique key and the cursor/`BackfillDay` rules.
- **Backfill request (AC-9.1 to 9.7):** validation in `RequestBackfill`: office in `UNIS_OFFICES`; dates real, ordered, not future, not before `ATTENDANCE_BACKFILL_START_DATE`; span within `ATTENDANCE_BACKFILL_MAX_DAYS` (default 366, OQ-A1); span over 31 days needs the confirmation and `manage_large_backfill`. The overlap check runs inside a transaction holding a PostgreSQL advisory lock for that office, so two simultaneous submits cannot both pass. "All offices" creates one job per office. The job enqueues the existing month-by-month chain with `job_id`. Nothing creates a job except this use case, and nothing calls it from migrations, beat or startup.
- **Job lifecycle:** `queued` on creation; `running` when its first chunk starts; each finished day updates `days_done` and `rows_inserted` through `on_day`; `done` when the last chunk finishes without a failed day; `failed` (with `failed_day`, `last_error_kind`) when a chunk raises; `cancelled` when `should_continue()` sees `cancel_requested`, after the day in progress. Resume sets `queued` and enqueues from the first not-done day. Re-check mode ignores the "day is done" skip for the requested range only.
- **Mismatch fix path:** the reconciliation pages offer a prefilled backfill form with re-check on (AC-10.3, 9.6); they never write.

### 13a.5 Sync trigger, results and audit
- `TaskEvent` is created as `queued` when an admin action publishes (event id = the Celery task id) and as `running` by the `task_prerun` signal for scheduled tasks. Signals (`task_prerun`, `task_postrun`, `task_failure`) update state, times and the small summary. This replaces `django-celery-results` (OQ-A7) and keeps `CELERY_TASK_IGNORE_RESULT = True`.
- Audit rows are written by the use cases in the same request, so a refused or failed action is also recorded. Schedule edits are audited from the admin save hook. Django's own `LogEntry` history is also kept for edited rows.

### 13a.6 Operational health
One page, one status per component, each with a **basis label** and a checked-at time. Checks are time-limited (about 3 s each), run in sequence with a hard overall limit, never raise to the page and never show hosts, ports, users, passwords or data.
| Component | Basis | How |
|---|---|---|
| Database | Live | `SELECT 1` |
| Broker (Redis) | Live | kombu connection plus `PING`, with response time |
| Workers | Live | `app.control.inspect(timeout=2).ping()` and `active_queues()`; lists responding workers and queues. No reply while a `BackfillJob` is running or a `TaskEvent` is running shows "no reply (a long task may be running)". A solo-pool worker answers only between tasks, so this wording matters. |
| Scheduler (Beat) | **Observed** | There is no way to ping Beat. Evidence: `last_run_at` of the heartbeat periodic task (updated by Beat when it dispatches) and its age against the interval. Stale after 3 missed intervals. Labelled "observed, not a live check". |
| Worker consumption | **Observed** | Last finished `attendance.heartbeat` `TaskEvent` and its age (proves Beat, broker and a worker worked together recently). |
| Schedule overdue | **Inferred** | Derived: now minus `last_run_at` greater than twice the interval. |
| UNIS office | Observed (passive) and Live (on demand) | Passive: last success and last error kind from `SyncCursor`. Button: `SELECT 1` through the adapter, time-limited, `trigger_sync` permission, audited. |
| Supervisor | Observed | Read of its status file (§13a.7): last update age and restart counts. |

### 13a.7 Reliable startup
- **Supervisor (`manage.py run_attendance_services`, no new dependency):** starts `celery worker --pool=solo -Q attendance_sync`, `celery worker --pool=solo -Q attendance_backfill` and `celery beat`, using `sys.executable`; on Windows each child is in its own process group. Waits up to 30 s for Redis; starts `redis-server` itself only when `REDIS_SERVER_PATH` is configured. Restarts a crashed child with exponential back-off (1 s up to 60 s, reset after 5 minutes of health). Rotates logs under `backend\logs\attendance\` (already ignored by `*.log`). Writes `supervisor-status.json` (pid, per-process state, restart count, last update) and a single-instance guard. Stops children cleanly on Ctrl+C, on a stop file or on `--stop`. `--status` prints the status without touching anything.
- **Windows development (AC-12.2):** `scripts\windows\attendance-service.ps1 install|uninstall|start|stop|status` registers a per-user scheduled task **"Timely Attendance Services"**: trigger "at log on" of the current user, hidden PowerShell running the supervisor with the project's venv, restart on failure, no time limit. It needs no administrator rights (to be verified in the first task; fallback: a Startup-folder shortcut). It is a launcher, not a job scheduler: the 5-minute jobs stay in Celery Beat. Limitation: it runs while that user is signed in.
- **Redis on Windows development:** the portable Redis 5 build is started by the supervisor when `REDIS_SERVER_PATH` is set. It is unofficial and has no service wrapper (OQ-A6).
- **Production (AC-12.3), documented templates only:** `deploy/systemd/` with units `timely-attendance-sync.service`, `timely-attendance-backfill.service`, `timely-attendance-beat.service` (and a note to use the distribution's Redis service): `User=`, `EnvironmentFile=`, `WorkingDirectory=`, `After=network-online.target postgresql.service redis.service`, `Restart=always`, `RestartSec`, logs to the journal. `deploy/windows-service.md` describes the Windows-server option through NSSM or WinSW, which would be a new tool and needs its own approval (OQ-A4). These files are not applied anywhere. Hosting stays OPEN.
- **Options considered:**
  | Option | Verdict |
  |---|---|
  | Supervisor command + per-user at-logon task | **Proposed** for Windows development: automatic, no admin, no new tool, restarts crashed processes. |
  | NSSM / WinSW Windows service | Always on and survives sign-out, but needs administrator rights and a new tool: option for Windows servers (OQ-A4). |
  | One process: `celery worker -B --pool=threads -c 4 -Q both` | Fewer processes, but Beat inside a worker is discouraged for production and threads share one process: not chosen; may be measured as a fallback. |
  | OS cron / Task Scheduler running each job | Rejected by the owner's goal (jobs stay in Beat). |
  | systemd units (Linux) | **Proposed** reference for production. |

### 13a.8 Security
- **AuthZ:** all attendance admin pages require `is_staff` and the matching permission from spec §4; superusers pass. The permission check lives in each action and view (not only in the menu), returns 403 and queues nothing. Actions are POST only with Django CSRF protection. Which groups hold the permissions is the owner's decision (OQ-A8). The generic django-celery-beat admin pages stay superuser-only (OQ-A2); its "Run selected tasks" action bypasses our audit, so attendance administrators are not given that permission.
- **Input validation:** office from the configured list, dates and spans as in §13a.4, job and run ids looked up server-side; no free-text task names, SQL or paths.
- **Audit:** every operation of §13a.5 writes an `OperationAudit` row (including refusals). Specific security audit events stay OPEN (D-30).
- **Data minimisation:** pages and records contain counts, dates, office codes and error kinds only.
- **Secrets:** no secret is read for display. The UNIS test goes through the adapter and shows only success or an error kind. The supervisor's logs contain process state, not environment values.

### 13a.9 Tech choices and dependencies
| Decision | Options | Chosen | Status |
|---|---|---|---|
| Task results | `django-celery-results` (new package); own `TaskEvent` | Own `TaskEvent` | PROPOSED (OQ-A7) |
| Next-run time | read from Beat; estimate from schedule | Estimate, labelled | PROPOSED |
| Beat liveness | no ping exists; heartbeat evidence | Heartbeat task + Observed label | PROPOSED |
| Duplicate-backfill guard | exclusion constraint (needs an extension); advisory lock | Advisory lock inside a transaction | PROPOSED |
| Process supervision | NSSM / WinSW; own supervisor | Own supervisor + OS launcher | PROPOSED (OQ-A4) |
| Admin custom pages | separate Next.js UI; Django Admin | Django Admin | CONFIRMED by the owner's request |
**New dependencies: None.** New repository folders: `scripts/windows/` and `deploy/` (documentation and templates; PROPOSED). `.gitignore` already ignores `*.log`.

### 13a.10 Traceability (A-1)
| Spec item | Plan |
|---|---|
| US-7, AC-7.1 to 7.4 | §13a.3 (`TaskEvent`), §13a.4 (schedule and executions pages), §13a.5 |
| US-8, AC-8.1 to 8.4 | §13a.4 (sync cursors, runs, guard, retry), §13a.3 (`SyncRun` columns) |
| US-9, AC-9.1 to 9.7 | §13a.4 (backfill jobs), §13a.2 (callbacks), §13a.3 (`BackfillJob`) |
| US-10, AC-10.1 to 10.3 | §13a.4 (reconciliation and summary) |
| US-11, AC-11.1 to 11.4 | §13a.6 |
| US-12, AC-12.1 to 12.4 | §13a.7 |
| US-13, AC-13.1 to 13.4 | §13a.8, §13a.5, §13a.2 (boundary unchanged) |

### 13a.11 Testing strategy (A-1)
- **Use cases (fakes):** trigger guard (queued, running, expired, lock held), retry rules, backfill validation table (bad office, bad dates, future, before start, over cap, over 31 days without confirmation or permission), overlap refusal including two simultaneous submits, lifecycle transitions, cancel between days, resume from first unfinished day, re-check mode, callbacks default to no-ops (approved tests unchanged).
- **Admin (Django test client, real PostgreSQL):** permission matrix per page and action (anonymous, staff without permission, staff with each permission, superuser): 403 or redirect and nothing queued; POST-only and CSRF; schedule page shows only `attendance.*`, refuses unknown task names, deleting default jobs and out-of-range intervals; estimated next run is labelled; actions publish through a fake publisher; broker-down path leaves no queued event; audit rows for success, refusal and failure; filters and summary numbers; no EID, RFID, host or password in any page (response scan).
- **Health:** each component with fake broker, fake inspect and fake clock covering Live, Observed, Inferred, stale heartbeat, no reply while a backfill runs, broker down, time-out (check never raises, page renders); response scan for secrets.
- **Signals and tasks (eager):** `TaskEvent` states for success and failure; heartbeat and housekeeping (pruning by retention, queued events expired).
- **Supervisor:** child-process fakes (small Python scripts) to test start, crash restart with back-off, back-off reset, clean stop, single-instance guard, status file, Redis-wait and optional Redis start; no real Celery needed.
- **Boundary:** the existing boundary test must still pass; `attendance.public` unchanged (a test compares its exported names).
- **Static checks:** `manage.py check`, `makemigrations --check`, `manage.py test attendance accounts about core`.
- **Manual (reported separately, never Passed until run):** owner walks through every admin page; trigger sync for MHK and RAOWA from admin; request a one-day backfill from the form and watch progress; submit an overlapping request (refused); cancel and resume; stop the worker and Redis and read the health page; sign in as a staff user without permission; run the supervisor, kill a child and see it restart; install the sign-in task, sign out and in again (or restart) and see the next 5-minute sync happen without terminals; review the systemd templates. A full historical backfill is **not** part of any check.

### 13a.12 Risks and mitigations (A-1)
- A solo-pool worker cannot answer a ping during a long task → wording "no reply (a long task may be running)" and use of the job state; not a "down" claim.
- Beat cannot be pinged → shown as Observed through the heartbeat, never as Live.
- A per-user logon task does not run before sign-in or after sign-out → documented limitation; Windows service option (OQ-A4) and Linux systemd for production.
- Admin actions that block on a dead broker → `apply_async(retry=False)`, short timeouts, error page, tested.
- A lost queue message leaves a "queued" marker → expiry after 15 minutes, housekeeping.
- A superuser can still bypass the attendance guard via the generic Beat "Run selected tasks" → the office lock still prevents concurrent processing; documented; assign no one else that permission.
- Table growth from the 1-minute heartbeat → 2-day retention and daily housekeeping.
- Cancel is cooperative → stops after the current day (about seconds to a minute); documented in the UI text.
- Supervisor bugs could hide worker crashes → status file, restart counts and the health page surface them.
- Converting `admin.py` to a package risks regressions → existing read-only admin tests must keep passing.

### 13a.13 Constitution check (A-1)
| Principle | Compliant? | Notes |
|---|---|---|
| P1 | Pending | A-1 changes approved documents; it needs owner approval before any work (workflow §5). |
| P2 | Yes | All items PROPOSED; open points OQ-A1 to OQ-A8 in spec §10. |
| P3 | Yes | Everything stays inside `attendance`; no other module touched; `attendance.public` unchanged. |
| P4 | Yes | UNIS only through the adapter (the connection test is a harmless read). |
| P5 | Yes | Server-side authorisation by permission, validated input, audit log, no data or secrets in pages, logs or records. |
| P6 | Yes | Strategy §13a.11; manual checks reported separately. |
| P7 | Yes | No new dependency; new folders and any Windows service wrapper need approval. |
| P8 | Yes | Admin pages are Django; no Next.js, no new HTTP API; the module boundary is unchanged. |

### 13a.14 Open points for the owner (A-1)
OQ-A1 to OQ-A8 in spec §10, plus: approve the new top-level folders `scripts/windows/` and `deploy/`; approve converting `attendance/admin.py` into a package; confirm that task results are not stored through `django-celery-results`.

## 13b. Amendment A-2 — Setup page in Django Admin (APPROVED 2026-10-15; implemented)
Implements spec §3b (US-14).
- **Shared code:** `infrastructure/setup.py` with `SetupService`: `status()` returns three step results; `run_schedule()`, `run_start_points(office_or_all, from_date)` and `run_partitions()` do the work. `ensure_jobs` (schedule.py) and `partitions.ensure_partitions` are reused; `partitions.missing_partitions` is new (read-only). The management commands `setup_attendance_schedule` and `ensure_partitions` stay as they are; `init_forward_sync` keeps its overwrite behaviour, while the page only fills offices without a cursor.
- **Admin:** unmanaged placeholder model `AttendanceSetup` (no table, like `OperationsHealth`), admin `admin/setup.py`, template `admin/attendance/setup.html`. Permission `manage_schedule`. POST actions: `schedule`, `start_points`, `partitions`; CSRF applies.
- **Audit:** three new `OperationAudit.Action` values (`setup_schedule`, `setup_start_point`, `setup_partitions`); migration 0004 (choices + unmanaged model, no data change).
- **Status rules:** schedule = Done when all four jobs exist, else Needs action (lists missing names); start points = Done when every configured office has a cursor, else Needs action; partitions = Done when none are missing from 2019-01 to 3 months ahead and the default partition is empty, Problem when the default partition holds rows.
- **Tests:** SetupService (idempotent, no overwrite, validation, missing partitions), admin (permission refusal, GET status, POST actions, CSRF/POST-only, audit, bad office/date), boundary test unchanged.
- No new dependency, no infrastructure change.

## 13c. Amendment A-3 ? Step-ordered menu and README (APPROVED 2026-10-15; implemented)
Implements spec ?3c. `attendance/site.py` (`TimelyAdminSite.get_app_list` reorders and numbers the attendance entries) is the project's default admin site through `attendance/admin_config.py` (`TimelyAdminConfig`, set in `INSTALLED_APPS` in place of `django.contrib.admin`; the supported Django mechanism). Only the displayed menu names and order change. `backend/attendance/README.md` is new. Test: `tests/test_menu_order.py`. No new dependency.

## 13d. Amendment A-4 ? Raw punch data menu (APPROVED 2026-10-15; not yet implemented)
Implements spec ?3d (US-16).
- **Model access (as built):** no ORM model of the partitioned table (the admin does not support composite primary keys). A placeholder `RawPunch` (unmanaged, no table) hosts the pages, and `infrastructure/persistence/punch_editor.py` (`PunchEditor`) reads and updates `attendance_punch` with raw SQL, next to `PunchRepository`. Rows are addressed by a URL-safe encoded key. Nothing is exported by `attendance.public`.
- **Admin `admin/punches.py`:** list with required date range (default today), office/terminal filters, EID search (exact), ordered by date and time descending, no total-count query (`show_full_result_count = False`), small pages. Detail form edits `date`, `time`, `rfid` and `geolocation` only; office, eid and terminal are `readonly_fields` and rejected if posted; `has_add_permission` and `has_delete_permission` are False; no actions. Save runs, in one transaction, `SELECT ... FOR UPDATE` of the row by its key, a check that the new key does not exist (refused otherwise, AC-16.9), a check that a partition exists for the new date, a single `UPDATE ... WHERE <old key>` that sets only the four editable columns and `updated_at` (PostgreSQL moves the row between partitions when the date changes), and the log row (with the original key, old and new values).
- **Audit and re-sync guard:** new table `PunchEditLog` (at, actor id and name, office, eid, terminal, field, old value, new value, and the original and new date and time), indexed on the original key (office, eid, terminal, original date, original time) and on both dates. The table is never purged by housekeeping (the guard needs it), read-only admin, migration 0005. Needs `view_punches`.
- **Permissions:** `view_punches` and `edit_punches`, added to `OperationAudit.Meta.permissions` (migration 0005) and checked server-side on every request.
- **Re-sync protection (AC-16.8):** the punch write path (`PunchRepository` bulk insert via temp table) gets one more anti-join: rows whose original key exists in `PunchEditLog` as a moved-away key are not inserted. This is the only change to existing sync code; the idempotency and the unique key stay as they are. A test covers forward sync and backfill after a date edit.
- **Reconciliation hint (AC-16.6):** the reconciliation admin page adds a read-only column 'edited in/out' per day, counted from `PunchEditLog` (an indexed query per page, only for the days shown). Stored reconciliation rows are not changed.
- **Edited marker:** an `edited` boolean column is not added to the partitioned table; "edited" is derived from the existence of a `PunchEditLog` row for the key (shown on the detail page only), so no change to the 50M-row table.
- **Tests:** permission refusal for list, detail, save and POST; office, eid and terminal cannot change by crafted POST; date/time edit moves the row, is refused on a collision or a missing partition, and is atomic; sync and backfill after a date edit do not bring back the original punch; reconciliation page shows edited in/out; validation; audit record with old and new value; counts unchanged; sync after an edit does not overwrite; no delete or add; filters require a date range; boundary test passes.
- **Security notes:** EID and RFID are personal data (P5): visible only with `view_punches`; `PunchEditLog` is not exposed anywhere else; no value is logged to files.
- No new dependency. Decision D-66 recorded as PROPOSED.

## 14. Change Log
| Date | Change | Reason | Approved by |
|---|---|---|---|
| 2026-10-14 | §8 package table: `redis` client pinned `6.4.0` instead of `8.1.0` (8.1.0 uses RESP3, failed against the Windows Redis 5 build, and is outside kombu's supported `redis<6.5`). Same approved package, different version. | Found during the first real worker run (task T22) | Owner request to install and run Redis (conversation); formal re-approval pending |
| 2026-10-15 | **Amendment A-1 (PROPOSED):** added §13a (admin-managed operations, health, supervised startup, security and audit). §3 gains operational tables, §10 gains tests, §11 gains risks. No change to §2 to §9 behaviour or to `attendance.public`. | Owner wants to manage scheduling, sync, backfill and monitoring from Django Admin and have the background processes start reliably | Pending owner |
| 2026-10-15 | **Amendment A-2 (APPROVED):** added ?13b (setup page: SetupService, unmanaged AttendanceSetup model, migration 0004, three audit actions) | Spec ?3b | Project owner, 2026-10-15 |
| 2026-10-15 | **Amendment A-3 (APPROVED):** added ?13c | Spec ?3c | Project owner, 2026-10-15 |
| 2026-10-15 | **Amendment A-4 (APPROVED):** added ?13d | Spec ?3d | Project owner, 2026-10-15 |
---
**Status:** Approved (base plan, 2026-10-14; Amendments A-1, A-2, A-3 and A-4, 2026-10-15) · **Approved by:** Project owner (`PLAN APPROVED`, as written, including the proposals and open points in §13 and the new dependencies and Redis listed in §8; A-1 approval 2026-10-15 with all proposed defaults) · **Date:** 2026-10-15
