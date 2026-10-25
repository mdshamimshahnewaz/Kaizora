# Task Breakdown — Attendance Sync

> **Purpose:** small, ordered, verifiable tasks that implement the approved `plan.md` (approved 2026-10-14) for the approved `spec.md`.
> **Location:** `specs/004-attendance-sync/tasks.md`.
> **Approval does not authorise implementation.** Implementation starts only after the owner approves this list **and** gives a separate explicit instruction to implement (`docs/decisions.md` D-6).

## Conventions
- `[ ]` pending, `[x]` done, `[~]` in progress, `[!]` blocked (explain why). Order = execution order. Each task cites the plan section and spec items.
- Backend commands from `backend\`: `.\.venv\Scripts\python.exe manage.py check | makemigrations --check | test attendance | test accounts about core`.
- No `.env` file is read or edited by the agent. Owner-only steps are marked **[Owner]**. The UNIS credentials and Redis installation are owner steps.
- Dependencies are installed only after T1 confirms compatibility; versions are pinned in `backend/requirements.txt`.
- Punch data is never written to logs, test output or documents (P5). Tests use synthetic data only.

## Preconditions
- [!] **T0 — [Owner] Provide the environment** _(depends on: none)_
  - Implements: Plan §6, §8, §13
  - Done when: the owner has installed a native Redis (OQ-P1: Memurai or another build) and has added to `backend\.env` the `UNIS_*` values for MBD, MHK and RAOWA (read-only logins) and `REDIS_URL`. Needed only for manual checks (T22); automated tests do not need them. Blocked until the owner does this.

## Foundation
- [x] **T1 — Verify and install new dependencies** _(depends on: none)_
  - Note: installed `celery` 5.6.3, `redis` 8.1.0, `mssql-python` 1.16.0 and `django-celery-beat` 2.9.0. `django-celery-beat` declares `Django<6.1` (pip downgraded Django during the install; restored to 6.1.2). Verified to work on 6.1.2; owner decided to keep it via `requirements-beat.txt` with `--no-deps` (D-62). Transitive packages added to `requirements.txt`: amqp, azure-core, azure-identity, billiard, click, click-didyoumean, click-plugins, click-repl, cron-descriptor, django-timezone-field, kombu, msal, msal-extensions, mssql-python-odbc, mssql-python-rs, packaging, prompt_toolkit, python-crontab, python-dateutil, six, typing_extensions, tzlocal, vine, wcwidth.
  - Implements: Plan §8, Risks
  - Done when: `celery`, `django-celery-beat`, `redis` and `mssql-python` are installed in the project venv and pinned in `requirements.txt`; `manage.py check` passes on Django 6.1 / Python 3.14; an isolated eager-task smoke test and `django_celery_beat` migrations apply; any incompatibility is stopped and reported to the owner (fallback decisions are the owner's). Installed transitive packages are listed in this task's note.
- [x] **T2 — Create the `attendance` app skeleton and settings** _(depends on: T1)_
  - Implements: Plan §2, §6 configuration
  - Done when: `attendance/` has `domain/`, `application/`, `infrastructure/`, `public.py`, `models.py`, `admin.py`, `tests/`; `attendance` and `django_celery_beat` are in `INSTALLED_APPS`; `config/celery.py` and `config/__init__.py` load the Celery app (JSON serializer only, `CELERY_` namespace, broker from `REDIS_URL`, queues `attendance_sync` and `attendance_backfill`, acks late, time limits); settings read `UNIS_OFFICES` and per-office `UNIS_<OFFICE>_*` and the throttle value from the environment with safe defaults; `.env.example` lists the new names without values; `manage.py check` passes without any UNIS or Redis present.

## Domain and application
- [x] **T3 — Domain types and ports** _(depends on: T2)_
  - Implements: Plan §2, §6 (ports), Spec AC-D.1, AC-6.1
  - Done when: `Punch`, `Office`, `SyncWindow` value objects and the ports (`PunchSource`, `PunchRepository`, `ProgressRepository`, `Clock`, `OfficeLock`) exist as pure Python; neither package imports Django, Celery or a driver; no UNIS vocabulary appears.
- [x] **T4 — Window calculation and forward-sync use case** _(depends on: T3)_
  - Implements: Plan §5 forward sync, Spec AC-2.1–2.3, AC-3.2
  - Done when: `ForwardSync` computes the window (cursor second inclusive, following days to today in Asia/Dhaka), writes through the ports, advances the cursor only after the batch commits, isolates one office's failure from the others, and skips a busy office; unit tests with in-memory fakes pass.
- [x] **T5 — Backfill use case** _(depends on: T3)_
  - Implements: Plan §5 backfill, Spec AC-1.1–1.3, AC-3.3
  - Done when: `BackfillOffice` walks days oldest to newest, skips `done` days, marks failed days and stops for that office, resumes from the first not-done day, honours the range and the pause setting; fake-based tests pass.
- [x] **T6 — Reconciliation use case** _(depends on: T3)_
  - Implements: Plan §5 reconciliation, Spec AC-5.2
  - Done when: `ReconcileDay` records UNIS count vs local count and sets `is_mismatch` when local is lower; tests pass.

## Persistence
- [x] **T7 — ORM models and schema migration** _(depends on: T2)_
  - Implements: Plan §3 (cursor, backfill day, run, reconciliation), Spec AC-5.1
  - Done when: the four small tables exist with the specified fields and unique constraints; `0001` applies on PostgreSQL; no personal data is stored in them.
- [x] **T8 — Partitioned punch table migration** _(depends on: T7)_
  - Implements: Plan §3 (punch table), Spec AC-3.1, AC-D.1
  - Done when: a RunSQL migration creates `attendance_punch` partitioned by month on `date` with the specified columns, unique key `(office, eid, date, time, terminal)`, index `(eid, date, time)`, monthly partitions from 2019-01 to the current month plus 3, and the default partition; it is reversible and applies in the test database.
- [x] **T9 — Partition maintenance** _(depends on: T8)_
  - Implements: Plan §3, §4.3
  - Done when: `ensure_partitions` creates missing future partitions idempotently and reports whether the default partition holds rows; tests cover idempotency.
- [x] **T10 — Punch repository** _(depends on: T8)_
  - Implements: Plan §3, §4.2, Spec AC-3.1, AC-3.2, AC-4.1
  - Done when: bulk insert uses a temp table and `INSERT ... ON CONFLICT DO NOTHING` and returns the inserted count; day insert and cursor update share one transaction; keyset-paginated reads by EIDs, office and date range work in the specified order; real-PostgreSQL tests cover idempotency, terminal-in-key, rollback, RFID leading zeros and cursor pagination.
- [x] **T11 — Progress, run records and office lock** _(depends on: T7)_
  - Implements: Plan §5 (lock, runs), Spec AC-2.3, AC-3.3, AC-5.1, AC-5.3
  - Done when: repositories for cursor, backfill days, runs and reconciliation exist; the per-office PostgreSQL advisory lock is acquired with try-lock and always released in `finally`; run records hold only office, dates, counts, result and an error kind; tests include two competing lock holders.

## External adapter
- [x] **T12 — UNIS adapter** _(depends on: T3, T1)_
  - Implements: Plan §6, Spec AC-6.1, AC-6.2, AC-D.1–D.3
  - Done when: `PunchSource` is implemented with the parameterised, read-only query, per-office config, database-name validation (`^[A-Za-z0-9_]+$`), `ApplicationIntent=ReadOnly`, 10 s connect and 60 s query timeouts, chunked reads, mapping of `L_UID/C_Date/C_Time/C_Name/C_Card` (RFID kept as text, empty to NULL), skipping and counting malformed rows, and exceptions wrapped into kind-only errors; tests with a mocked driver show no write statements and no credentials or host in any exception or log text.

## Public interface and commands
- [x] **T13 — Public interface** _(depends on: T10, T11)_
  - Implements: Plan §4.2, Spec AC-4.1, AC-4.2, AC-5.3
  - Done when: `public.py` exposes the frozen DTOs, `list_punches`, `get_sync_status` and `get_reconciliation` with argument validation (required date range, limit max 1000, 31-day span when no EID filter) and returns no ORM objects or driver exceptions; tests cover validation and paging.
- [x] **T14 — Boundary test** _(depends on: T13)_
  - Implements: Plan §10, Spec AC-4.3
  - Done when: an `ast`-based test fails if any file outside `attendance/` imports anything from `attendance` other than `attendance.public`, or if `attendance` imports another local app; the test passes now and is shown to fail on a deliberate violation.
- [x] **T15 — Management commands** _(depends on: T4, T5, T9, T10, T12)_
  - Implements: Plan §4.3, Spec AC-1.3
  - Done when: `backfill_attendance`, `init_forward_sync` and `ensure_partitions` work per the plan (office and date range options, inline vs `--enqueue`, default forward cursor = start of today in Asia/Dhaka) with tests using fakes.

## Celery
- [x] **T16 — Celery tasks** _(depends on: T4, T5, T6, T11, T12)_
  - Implements: Plan §5, §8
  - Done when: `forward_sync_all`, the `backfill_office` chain and `ensure_partitions_task` are thin tasks in `infrastructure/tasks.py` routed to the right queues with JSON arguments of office codes and dates only; per-office errors never fail the whole forward task; eager-mode tests pass.
- [x] **T17 — Beat schedule setup** _(depends on: T16)_
  - Implements: Plan §4.3, §5
  - Done when: `setup_attendance_schedule` idempotently creates the 5-minute forward-sync entry and the daily partition entry in django-celery-beat; running it twice leaves one of each (test).
- [x] **T18 — Read-only admin** _(depends on: T7)_
  - Implements: Plan §7, Spec AC-5.1–5.3
  - Done when: `SyncRun`, cursor, backfill day and reconciliation are visible in Django admin with no add, change or delete permission; no punch admin exists.

## Docs
- [x] **T19 — Update docs** _(depends on: T1, T2, T17)_
  - Implements: Plan §13 (OQ-P6)
  - Done when: `docs/tech-stack.md` lists the new packages, env variable names, the module and the worker/beat/Redis commands for Windows (`--pool=solo`, two queues); `docs/decisions.md` records D-40 for attendance, the time-zone exception (AC-D.2) and the D-22 module structure as owner-approved with date; `docs/architecture.md` §4 notes the `attendance` module. Nothing else in `docs/` changes.

## Tests and validation
- [x] **T20 — Backend tests for all acceptance criteria** _(depends on: T3–T18)_
  - Implements: Plan §10
  - Done when: `manage.py test attendance` passes and covers every AC that can be tested automatically, plus the secrets test (AC-6.2); `manage.py test accounts about core` still passes; `makemigrations --check` is clean; `manage.py check` passes.
- [x] **T21 — Large-load performance check** _(depends on: T10)_
  - Implements: Plan §10 manual list, Spec §7
  - Done when: with synthetic data only, a day batch insert and a keyset read on a multi-million-row test load are timed and the numbers recorded in `validation.md` (no pass/fail target exists, D-29 OPEN); the load is removed afterwards.
- [~] **T22 — Manual verification with real systems (executed separately)** _(depends on: T0, T20)_
  - Mostly done (validation.md §2a): Redis, real workers and Beat; real connection, column types, sample day, one-day backfill, scheduled forward sync and reconciliation for **MBD, MHK and RAOWA** (MBD became reachable on 2026-10-15). Still open: stopping a UNIS server mid-run (simulated only) and the multi-year backfill (needs explicit owner approval). The TLS certificate decision is closed (D-63).
  - Implements: Plan §10 manual list
  - Done when: each item is Passed, Partial or Not executed with a note: read-only connection to each UNIS server and confirmation of the `C_Date`/`C_Time` types; counts of one day compared with the legacy data; a one-day backfill and resume after stopping; Redis + two workers + beat running over several 5-minute cycles on Windows; stopping UNIS and Redis mid-run; reconciliation flags a forced mismatch. **[Owner]** runs or supervises steps that need credentials; the agent never reads or prints credentials or real punch data.
- [x] **T23 — Validation pass** _(depends on: T20–T22)_
  - Produces: `specs/004-attendance-sync/validation.md` (from `sdd-templates/validation-checklist-template.md`), marked `Ready for approval`
  - Done when: every AC is Passed with executed evidence or explicitly Deferred or Not executed with a reason; planned and executed validation are reported separately; `specs/README.md` is updated.

## Amendment A-1 tasks (APPROVED 2026-10-15, NOT yet authorised for implementation; T24 to T42)
> Implements plan §13a for spec US-7 to US-13. Implementation starts only after the owner gives a separate explicit instruction (D-6). No task starts, schedules or simulates the 2019-to-today backfill; manual checks use one-day ranges at most. No commit is made unless the owner asks. T22 stays Partial and the feature is not closed until the real UNIS checks and the A-1 manual checks are executed and recorded.

### Foundation and data
- [x] **T24 — Models, permissions and migration `0003`** _(depends on: approval of A-1)_
  - Implements: Plan §13a.3, Spec AC-9.4, AC-7.4, AC-13.1, AC-13.3
  - Done when: `BackfillJob`, `TaskEvent`, `OperationAudit` exist; `SyncRun` has `triggered_by`, `celery_task_id`, `retry_of`; the six permissions exist; the migration applies on PostgreSQL and on a database with existing rows; `makemigrations --check` is clean; no personal data field exists.
- [x] **T25 — Settings and ports** _(depends on: T24)_
  - Implements: Plan §13a.2, §13a.4
  - Done when: settings exist for the backfill span limit (default 366), the large-range threshold (31), retention periods (30 / 2 / 365 days), queued-event expiry (15 minutes), health timeouts and `REDIS_SERVER_PATH`, all with safe defaults and listed in `.env.example` without values; ports `JobRepository`, `TaskPublisher`, `AuditLog` exist in `application/ports.py` and import no Django.

### Application and tasks
- [x] **T26 — Operations use cases** _(depends on: T25)_
  - Implements: Plan §13a.4, Spec AC-8.1–8.3, AC-9.1–9.7, AC-13.2, AC-13.3
  - Done when: `TriggerSync`, `RetryRun`, `RequestBackfill`, `ResumeBackfill`, `CancelBackfill` implement the validation, caps, duplicate and overlap rules and write audit entries for success, refusal and failure; fake-based tests cover every rule in plan §13a.11, including two simultaneous backfill requests.
- [x] **T27 — Backfill callbacks and job progress** _(depends on: T26)_
  - Implements: Plan §13a.2, §13a.4 (lifecycle), Spec AC-9.4–9.6
  - Done when: `BackfillOffice` accepts optional `should_continue` and `on_day` callbacks with no-op defaults and its approved tests pass unchanged; a job moves queued, running, done, failed or cancelled as specified; cancel stops after the day in progress; re-check mode re-reads loaded days only for the requested range.
- [x] **T28 — Tasks, publisher and signals** _(depends on: T26)_
  - Implements: Plan §13a.2, §13a.5, Spec AC-7.4, AC-8.1
  - Done when: `forward_sync_offices` and a `job_id` argument on `backfill_office` exist; the publisher uses `apply_async(retry=False)` and returns a clean "broker unavailable" answer; signals keep `TaskEvent` states and the small summary current for scheduled and manual runs; `attendance.heartbeat` and `attendance.housekeeping` exist and are added to `setup_attendance_schedule` (idempotent); eager-mode tests pass; no result backend is introduced.

### Admin pages
- [x] **T29 — Admin package and shared guards** _(depends on: T24)_
  - Implements: Plan §13a.2, §13a.8, Spec AC-13.1, AC-13.4
  - Done when: `attendance/admin.py` is a package whose four existing read-only registrations behave exactly as before (existing tests pass); a shared permission helper, POST-only action wrapper and a response scanner for tests exist.
- [x] **T30 — Schedule and task-execution pages** _(depends on: T28, T29)_
  - Implements: Plan §13a.4, Spec AC-7.1–7.4
  - Done when: the attendance schedule page lists only `attendance.*` jobs with last run, total runs and an estimated next run labelled "estimated"; only enabled and interval are editable within the limits; no add, no delete of default jobs, no free-text task name; changes are audited and take effect without a restart (verified against Beat); the task-execution list filters by task, state and date.
- [x] **T31 — Sync operations in admin** _(depends on: T26, T28, T29)_
  - Implements: Plan §13a.4, Spec AC-8.1–8.4, AC-11.3 (connection test)
  - Done when: "Sync selected offices now", "Test UNIS connection" and "Retry selected failed runs" work with the permission checks, the duplicate guard and the broker-down message; run history shows who triggered each run and the retry link; every action writes an audit row.
- [x] **T32 — Backfill job pages** _(depends on: T27, T28, T29)_
  - Implements: Plan §13a.4, Spec AC-9.1–9.7
  - Done when: the add form validates every rule, requires the confirmation and the large-backfill permission above 31 days, refuses overlaps, queues the chain and shows progress, failed day and error kind; Resume and Cancel work; nothing outside this form or its use case can create a job (test).
- [x] **T33 — Reconciliation pages** _(depends on: T29)_
  - Implements: Plan §13a.4, Spec AC-10.1–10.3
  - Done when: the read-only list shows source, local, difference and flags with the three filters; the per-office summary shows last success, last error, data as of, open mismatches and links, including a prefilled backfill form with re-check on; no edit or fix action exists.
- [x] **T34 — Operational health page** _(depends on: T28, T29)_
  - Implements: Plan §13a.6, Spec AC-11.1–11.4
  - Done when: each component shows its basis label (Live, Observed or Inferred) and checked-at time; checks are time-limited and never fail the page; "no reply (a long task may be running)" appears when applicable; the page contains no host, port, user, password, EID or RFID (response-scan test).
- [x] **T35 — Audit log page and retention** _(depends on: T28, T29)_
  - Implements: Plan §13a.3, §13a.4, Spec AC-13.3
  - Done when: the audit list is read-only and filterable; housekeeping prunes `TaskEvent`, heartbeat evidence and audit rows by their retention settings and expires stale queued events; tests use a fake clock.

### Reliable startup
- [x] **T36 — Supervisor command** _(depends on: T28)_
  - Implements: Plan §13a.7, Spec AC-12.1
  - Done when: `manage.py run_attendance_services` starts the two workers and Beat, waits for Redis and starts it only if `REDIS_SERVER_PATH` is set, restarts crashed children with back-off, rotates logs under `backend\logs\attendance\`, writes `supervisor-status.json`, enforces a single instance and stops cleanly; `--status` and `--stop` work; tests with child-process fakes pass.
- [x] **T37 — Windows auto-start scripts** _(depends on: T36)_
  - Implements: Plan §13a.7, Spec AC-12.2, AC-12.4
  - Done when: `scripts\windows\attendance-service.ps1` installs, removes, starts, stops and reports the per-user at-logon task without administrator rights (or the Startup-folder fallback is documented if that is not possible); the task starts the supervisor hidden; a manual run shows the processes up and a killed child restarting. The sign-out / restart behaviour is recorded in T41, not assumed.
- [x] **T38 — Production service templates** _(depends on: T36)_
  - Implements: Plan §13a.7, Spec AC-12.3
  - Done when: `deploy/systemd/` contains the three unit templates and `deploy/windows-service.md` describes the NSSM / WinSW option, both with environment file, user, order, restart policy and logs; clearly marked as templates; nothing is applied to any server and no new tool is installed.

### Docs, tests and validation
- [x] **T39 — Update docs** _(depends on: T30–T38)_
  - Implements: Plan §13a.7, §13a.9
  - Done when: `docs/tech-stack.md` replaces the manual three-terminal procedure with the supervisor, admin pages, permissions, new settings and the Windows auto-start commands; `docs/decisions.md` records the approved A-1 decisions (OQ-A1 to OQ-A8 outcomes) with dates; `docs/architecture.md` §4 mentions the admin operations of `attendance`; nothing else in `docs/` changes.
- [x] **T40 — Automated tests for A-1** _(depends on: T24–T38)_
  - Implements: Plan §13a.11, all A-1 ACs
  - Done when: every A-1 AC that can be tested automatically has a passing test (permission matrix, validation table, overlap, audit, health labels, scanners, supervisor); the approved 161 tests, the boundary test and a test that `attendance.public` still exports the same names pass; `manage.py check` and `makemigrations --check` are clean.
- [~] **T41 — Manual verification (executed separately)** _(depends on: T40; real UNIS checks of T22 for MBD remain open)_
  - Partly done (validation.md §2a): the real-system checks that an agent can run were executed and recorded. **Still for the owner:** the browser walkthrough of every admin page, a real sign-out/sign-in or restart with the auto-start task, a real mid-run cancel, the "Test connection" button on the real page, and a review of the production templates. No historical backfill was run.
  - Implements: Plan §13a.11 manual list
  - Done when: each item is Passed, Partial or Not executed with a note: the owner's walkthrough of every admin page; sync now for MHK and RAOWA; a one-day backfill from the form with progress, an overlapping request refused, cancel and resume; stopping the worker and Redis and reading the health page labels; a staff user without permission refused; the supervisor restarting a killed child; the sign-in task starting the services after sign-out and sign-in (and after a restart if the owner can do it) with the next 5-minute sync happening without terminals; review of the templates. No historical backfill is run. Agents never print credentials, hosts, EIDs or RFIDs.
- [x] **T42 — Validation update** _(depends on: T40, T41)_
  - Produces: updated `specs/004-attendance-sync/validation.md` (A-1 section, planned and executed separate), status `Ready for approval`; `specs/README.md` updated.
  - Done when: every A-1 AC is Passed with evidence or explicitly Partial, Deferred or Not executed with a reason, and the limitations for T22 (MBD) and the manual items are stated; the owner approves it separately.

## Amendment A-2 tasks (APPROVED 2026-10-15; implemented; T43 to T48)
- [x] **T43 — SetupService and missing_partitions** _(plan §13b)_ — Done when: status and the three actions work, idempotent, no cursor overwrite. Implements AC-14.2.
- [x] **T44 — Audit actions and migration 0004** — Done when: three audit actions and the unmanaged `AttendanceSetup` model migrate cleanly. Implements AC-14.4.
- [x] **T45 — Admin setup page and template with help text** — Done when: status, evidence, help text, POST buttons, `manage_schedule` check. Implements AC-14.1, AC-14.3.
- [x] **T46 — Tests** — Done when: service, admin, permission, validation and audit tests pass and existing tests still pass. Implements AC-14.2 to AC-14.5.
- [x] **T47 — Docs** — Done when: `docs/tech-stack.md` and `deploy/windows-service.md` mention the setup page as the first-time step.
- [x] **T48 — Validation update** — Done when: `validation.md` A-2 section lists executed and not executed checks, status `Ready for approval`.

## Amendment A-3 tasks (APPROVED 2026-10-15; implemented; T49 to T51)
- [x] **T49 ? Step-ordered Attendance menu** ? `attendance/site.py`, `attendance/admin_config.py`, settings. Implements AC-15.1.
- [x] **T50 ? Menu order test** ? `tests/test_menu_order.py`.
- [x] **T51 ? Module README** ? `backend/attendance/README.md`. Implements AC-15.2.

## Amendment A-4 tasks (APPROVED 2026-10-15; implementation authorised 2026-10-15; implemented; T52 to T60)
- [x] **T52 ? Unmanaged `Punch` model and `PunchEditLog` model, permissions, migration 0005** _(plan ?13d)_ ? Done when: migration applies, `makemigrations --check` clean, the partitioned table is untouched. Implements AC-16.5.
- [x] **T53 ? Raw punch list (filters, required date range, EID search, paging)** ? Done when: AC-16.1 and AC-16.2 hold. 
- [x] **T54 ? Detail and edit of date, time, rfid and geolocation; office, eid and terminal read-only; no add or delete** ? Done when: AC-16.3, AC-16.4, AC-16.9 hold (collision and missing-partition refusals, atomic move).
- [x] **T59 ? Re-sync protection in the punch write path** _(depends on: T52)_ ? Done when: AC-16.8 holds for forward sync and backfill, and the existing sync tests still pass.
- [x] **T60 ? Reconciliation page 'edited in/out' column** _(depends on: T52, T54)_ ? Done when: AC-16.6 hold: the column is correct and stored reconciliation rows are unchanged.
- [x] **T55 ? Edit log admin (read-only, `view_punches`)** ? Done when: every edit shows who, when, old and new value.
- [x] **T56 ? Menu entry and README/docs update** ? Done when: the Attendance menu, `backend/attendance/README.md` and `docs/decisions.md` (D-66) are updated.
- [x] **T57 ? Tests** ? Done when: the tests listed in plan ?13d pass and the existing suite still passes.
- [x] **T58 ? Validation update** ? Done when: `validation.md` A-4 section lists executed and not executed checks, status `Ready for approval`.

## Notes
- Out of scope per spec §9 (as amended): late or edited UNIS rows, HTTP API, end-user UI, geolocation values, employee linking, shift calculation, local edit or delete of punches, provisioning or operating a production server, starting the full historical backfill automatically, alerts by email or chat, `django-celery-results`.
- If T1 finds an incompatibility, implementation pauses and the owner decides the fallback (a plan change with re-approval).
- The full 2019-to-today backfill is operated by the owner after validation; it is not part of any task's "done" condition.
- Do not add tasks outside the approved plan; raise them for approval.

## Change Log
Changes after approval require re-approval and pause implementation (see `docs/sdd-workflow.md` §5).

| Date | Change | Reason | Approved by |
|---|---|---|---|
| 2026-10-15 | **Amendment A-1 (PROPOSED):** added T24 to T42 (admin-managed operations, health, supervised startup). T1 to T23 unchanged. | Owner wants to manage scheduling, sync, backfill and monitoring from Django Admin | Pending owner |
| 2026-10-15 | **Amendment A-2 (APPROVED):** added T43 to T48 (setup page in Django Admin) | Spec 3b, plan 13b | Project owner, 2026-10-15 |
| 2026-10-15 | **Amendment A-3 (APPROVED):** added T49 to T51 | Spec ?3c | Project owner, 2026-10-15 |
| 2026-10-15 | **Amendment A-4 (APPROVED):** added T52 to T60 | Spec ?3d | Project owner, 2026-10-15 |
---
**Status:** Approved (T0 to T23, 2026-10-14; Amendments A-1 T24 to T42, A-2 T43 to T48, A-3 T49 to T51 and A-4 T52 to T60, 2026-10-15) · **Approved by:** Project owner (`TASKS APPROVED` 2026-10-14; A-1 approval 2026-10-15) · **Date:** 2026-10-15 · **Implementation authorised by owner:** Yes for T0 to T23 (2026-10-14); **Yes for A-1 (T24 to T42), explicit `implement` instruction 2026-10-15**
