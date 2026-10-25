# Feature Spec — Attendance Sync

> **Purpose:** WHAT is being built and WHY, with no technical solution. Technical decisions are in `plan.md`.
> **Location:** `specs/004-attendance-sync/spec.md`. **Rules:** `docs/constitution.md` (P2, P3, P4, P5, P7, P8), `docs/architecture.md`.
> **Process note:** drafted in the conversation on 2026-10-14 and approved by the owner (`SPEC APPROVED`) as drafted. Items marked PROPOSED or OPEN were not changed by the approval; see §10.
> **Amendment A-1 (2026-10-15, APPROVED by the owner 2026-10-15):** the owner asked to manage scheduling, sync, backfill and monitoring from Django Admin and to keep the background processes running reliably. A-1 adds US-7 to US-13, AC-7.x to AC-13.x and the changes in §4 to §10 marked "(A-1)". Approval of A-1 does not authorise implementation (D-6). The approved base spec (US-1 to US-6) is otherwise unchanged.

## 1. Summary
An independent `attendance` module that copies punch records from UNIS (MSSQL, read-only) into Timely's own PostgreSQL. It has two jobs only: **(1) backfill** historical data (2019 → today) and **(2) forward sync** of new data every 5 minutes. Three UNIS servers are covered: **MBD, MHK, RAOWA**. The module owns its tables; other modules get data only through a public interface, so it can later become a microservice. No UI and no HTTP API in this feature. **[PROPOSED, approved with this spec]**

## 2. User Stories
- **US-1 (P0):** As the system owner, I want historical punches from 2019 loaded from all three UNIS servers, so that Timely has the full history.
- **US-2 (P0):** As the system owner, I want new punches synced every 5 minutes, so that Timely stays current.
- **US-3 (P0):** As the system owner, I want the sync to be safe to repeat, stop and resume, so that no punch is duplicated or lost.
- **US-4 (P0):** As another Timely module, I want to read punches only through a public interface, so that I never depend on attendance's tables.
- **US-5 (P1):** As an administrator, I want to see sync status per server (last success, last error, "data as of") and a count check of UNIS vs Timely per office/day, so that I can trust the data.
- **US-6 (P1):** As a developer, I want UNIS access isolated behind an adapter, so that UNIS can change without touching the rest.
- **US-7 (A-1, P0):** As an authorised administrator, I want to manage the scheduled attendance jobs (interval, on/off, last and next run, results) in Django Admin, so that I do not edit schedules by command line.
- **US-8 (A-1, P0):** As an authorised administrator, I want to trigger a sync for chosen offices, see the run history and safely retry failed runs from Django Admin.
- **US-9 (A-1, P0):** As an authorised administrator, I want to request a resumable backfill for an office and date range from a Django Admin form and follow its progress and failures, without anything ever starting a historical backfill by itself.
- **US-10 (A-1, P1):** As an authorised administrator, I want read-only views of source vs local counts, discrepancies, the last successful sync and related runs, so that I can judge data quality.
- **US-11 (A-1, P1):** As an authorised administrator, I want to see whether the broker, workers and the scheduler are available, and whether each status was checked now or only inferred.
- **US-12 (A-1, P0):** As the system owner, I want Redis, the sync worker, the backfill worker and the scheduler to start and keep running reliably in Windows development and in production without opening terminals or using OS cron for the jobs.
- **US-13 (A-1, P0):** As the system owner, I want every operational action restricted to authorised administrators, validated, protected against duplicate concurrent backfills and audited.

## 3. Acceptance Criteria
### US-1
- **AC-1.1:** Given a start date and an office, when backfill runs, then every UNIS punch from that date to today is stored, one day at a time.
- **AC-1.2:** Given backfill stopped midway, when it runs again, then it resumes at the first unfinished office/day without re-importing finished days.
- **AC-1.3:** Backfill can be limited to one office and a date range.

### US-2
- **AC-2.1:** Every 5 minutes, new punches from each office are read from the last synced point up to now and stored.
- **AC-2.2:** One office being unreachable does not stop the other offices.
- **AC-2.3:** Runs never overlap for the same office.

### US-3
- **AC-3.1:** A punch is unique by (office, EID, date, time, terminal); inserting it again changes nothing.
- **AC-3.2:** A failed batch stores nothing from that batch, and the progress point does not advance.
- **AC-3.3:** Backfill and forward sync never process the same office/day at the same time.

### US-4
- **AC-4.1:** Other modules can list punches (filter by EID list, date range, office; paged) and get sync status through the public interface only.
- **AC-4.2:** Returned data is plain read-only objects, never database models.
- **AC-4.3:** A test fails if any other module imports attendance internals, or attendance imports another module.

### US-5
- **AC-5.1:** Each run is recorded (kind, office, range, counts, result, error kind).
- **AC-5.2:** For each office/day, UNIS count and Timely count are recorded, and a mismatch is flagged.
- **AC-5.3:** Status reports per office the last successful sync and last failure.

### US-6
- **AC-6.1:** UNIS is accessed read-only; no UNIS vocabulary (`tEnter`, `L_UID`) appears outside the adapter.
- **AC-6.2:** UNIS host, database and credentials come from the environment only and never appear in logs, errors, or the repository.

### Data fidelity
- **AC-D.1:** Stored fields: EID, date, time, terminal, RFID (leading zeros kept), office, geolocation (empty for now), created/updated times.
- **AC-D.2:** Date and time are kept as local UNIS time (Asia/Dhaka), without UTC conversion. **[Owner-approved exception to the UTC convention in `docs/api-conventions.md`; to be recorded in `docs/decisions.md`.]**
- **AC-D.3:** Office is the UNIS server the punch came from.

## 3a. Amendment A-1 acceptance criteria (PROPOSED)
"Authorised administrator" means a staff user holding the Django permission named in §4 (superusers hold all). Admin pages are Django Admin pages of the `attendance` module; they are not a new HTTP API and not an end-user UI.

### US-7 Scheduler management
- **AC-7.1:** Given an authorised administrator, when they open the attendance schedule page, then each attendance job shows its name, task, queue, interval, enabled state, last run, total runs and an **estimated** next run (labelled "estimated", derived from the interval and last run, because only the scheduler knows the real time).
- **AC-7.2:** An administrator can enable or disable a job and change its interval; the change takes effect without restarting any process and is audited (AC-13.3).
- **AC-7.3:** The attendance schedule page accepts only the attendance jobs on a fixed allow-list; an arbitrary task name is refused. The default jobs (forward sync, partition check, heartbeat) can be disabled but not deleted from this page.
- **AC-7.4:** Each execution of an attendance task (scheduled or manual) is listed with task name, start and end time, outcome, counts and an error kind, filterable by task, outcome and date, containing no personal data. Retention of these records is a setting (OQ-A3).

### US-8 Sync operations
- **AC-8.1:** An administrator with the sync permission can select one or more configured offices and trigger a forward sync now. The page answers immediately ("queued"); the result appears later as a run record (the page never waits for UNIS).
- **AC-8.2:** A trigger for an office is refused with a clear message when a sync for that office is already queued or running, so no duplicate is created.
- **AC-8.3:** "Retry" is offered only for failed runs. A retried forward run continues from the office's saved cursor and a retried backfill run continues from its failed day; both are idempotent. Retry is refused when that office already has a newer successful run or an active run.
- **AC-8.4:** Run history is listed per office and kind with result, counts, error kind, who triggered it (a person, or "scheduled") and the retry link, and is read-only.

### US-9 Backfill management
- **AC-9.1:** The backfill form takes an office (one configured office or all) and a date range, and the server validates it: known office, valid dates, from not after to, not in the future, not before the configured start date (2019-01-01), and a span within the per-request limit (OQ-A1).
- **AC-9.2:** Submitting the form creates a backfill job and queues a resumable, month-by-month backfill on the backfill queue. Nothing creates a backfill without this explicit submit: not a migration, a schedule, startup or a retry of a forward run.
- **AC-9.3:** A request is refused when an active (queued or running) job for the same office overlaps the requested dates, so two backfills never run over the same office/day.
- **AC-9.4:** Each job shows its state (queued, running, done, failed, cancelled), days total / done / failed, rows inserted, the last error kind and the failed day, updated as days complete.
- **AC-9.5:** A failed or cancelled job can be resumed (it continues at the first unfinished day) and a queued or running job can be cancelled; cancel stops the job after the day in progress.
- **AC-9.6:** A job can optionally "re-check days already loaded" (default off), so a day flagged as a mismatch can be re-read; inserts stay idempotent.
- **AC-9.7:** A request longer than 31 days needs an extra confirmation and the separate large-backfill permission. The whole history from 2019 therefore needs several confirmed jobs; the system never splits and starts it automatically.

### US-10 Reconciliation views
- **AC-10.1:** A read-only list shows, per office and day, the source count, the local count, the difference, the mismatch flag and when it was checked, filterable by office, date range and mismatch only.
- **AC-10.2:** A per-office summary shows the last successful sync, the last error and its kind, the "data as of" moment, the number of open mismatches and links to the related runs.
- **AC-10.3:** These views have no edit or fix action. To correct a mismatch the administrator uses the backfill form (AC-9.6).

### US-11 Operational health
- **AC-11.1:** An operations health page shows, for the broker, the workers, the scheduler (Beat), the schedule and each UNIS office, one status each.
- **AC-11.2:** Every status carries a basis label and a "checked at" time: **Live** (checked when the page loaded or the button was pressed), **Observed** (the last recorded evidence and its age, for example the last scheduler tick or last heartbeat) or **Inferred** (derived from other facts). The page never shows a bare "OK" and never shows an inferred status as live.
- **AC-11.3:** The broker is checked live (PING with response time). Workers are checked live (control ping, listing the responding workers and their queues); when a worker does not reply while a backfill is known to be running, the status says "no reply (a long task may be running)" and not "down". The scheduler is **Observed** from the last time it dispatched the heartbeat job. Each UNIS office offers a "test connection" button that performs a harmless read (`SELECT 1`), is time-limited and refused for non-authorised users.
- **AC-11.4:** Checks are time-limited (a few seconds each), never fail the page, and show "unavailable" with a reason kind when infrastructure is down. The page never shows hosts, ports, user names, passwords, connection strings, EIDs or RFIDs.

### US-12 Reliable startup
- **AC-12.1:** One documented command starts and supervises the sync worker, the backfill worker and Beat, restarts a crashed process with back-off, and writes logs to files. It checks that Redis is reachable and, only if a Redis program path is configured, starts it.
- **AC-12.2:** In Windows development the supervisor starts automatically when the developer signs in, without administrator rights and without opening terminals, and there are documented commands to install, remove, start, stop and check it.
- **AC-12.3:** For production the repository documents ready-to-adapt service definitions (Linux systemd units; a Windows service option) covering order, environment file, run-as user, restart policy and logs. The production host remains an owner decision and the definitions are not applied to any server by this feature.
- **AC-12.4:** After the machine restarts and the developer signs in, the next scheduled forward sync happens without any manual command (checked on the development machine).

### US-13 Security and safety
- **AC-13.1:** Every operational page and action needs a staff user with the matching Django permission (view schedule, view health, trigger sync, manage backfill, manage large backfills, retry runs). A user without it gets a refusal and nothing is queued. Actions are POST-only and use Django's CSRF protection.
- **AC-13.2:** All inputs are validated on the server: the office from the configured list, dates, limits and job identifiers; no free-text task names or SQL are accepted.
- **AC-13.3:** Every manual trigger, retry, backfill request, resume, cancel, schedule change and connection test writes an audit record: who, when, action, office, date range, outcome and task or job id; no punch data or secrets.
- **AC-13.4:** The module boundary is unchanged: `attendance.public` remains the only interface for other modules, no attendance model or table is exposed to them, and the boundary test (AC-4.3) still passes.

## 3b. Amendment A-2 — First-time setup from Django Admin (owner request 2026-10-15; APPROVED by the owner 2026-10-15)

**Why.** Three one-time bootstrap steps still need the command line: `setup_attendance_schedule`, `init_forward_sync` and `ensure_partitions`. The owner wants them in Django Admin, with status and plain-language help, so anyone can see what is set up and what is missing.

### US-14 Setup page
- **AC-14.1:** A page **Attendance → Attendance setup** shows three steps: (1) Beat schedule (the four attendance jobs), (2) forward-sync start point per office, (3) monthly partitions. Each step shows a status (Done, Needs action, or Problem), the evidence for it (counts, dates, office codes only) and a short "what is this / when to do it / what happens if skipped" text. An overall line says whether the module is ready to sync.
- **AC-14.2:** Each step has a POST-only button that performs it. All three are idempotent. Step 1 keeps intervals and on/off states an administrator already changed. Step 2 only sets offices that have **no** start point (default: today, Asia/Dhaka, or an optional date that is not in the future); it never overwrites an existing start point. Step 3 creates the missing partitions only.
- **AC-14.3:** The page and the buttons need a staff user with the `manage_schedule` permission (no new permission). Inputs are validated on the server (office from the configured list, date format and range). A user without it is refused and nothing changes.
- **AC-14.4:** Every button press writes an audit record (who, when, action, office, outcome; no secrets or punch data).
- **AC-14.5:** The three commands keep working unchanged (the admin and the commands share one implementation). `attendance.public` and the module boundary are unchanged.
- **Out of scope:** changing an existing start point from the page (needs the command with its explicit warning), starting any backfill, starting Redis or the workers.

## 3c. Amendment A-3 ? Step-ordered Attendance menu and module documentation (owner request 2026-10-15; APPROVED 2026-10-15)
- **AC-15.1:** In Django Admin the Attendance menu lists the pages in working order: 1 Attendance setup, 2 Operations health, 3 Attendance schedule, 4 Sync runs, 5 Backfill jobs, 6 Reconciliations, then the read-only detail and log pages. Other apps' menus are unchanged. Permissions are unchanged.
- **AC-15.2:** `backend/attendance/README.md` documents the module (how it works, setup, running the processes, the admin steps, jobs, permissions, data, using `attendance.public`, backfill, troubleshooting).

## 3d. Amendment A-4 ? Raw punch data menu (owner request 2026-10-15; APPROVED 2026-10-15)

**Why.** The owner wants to see the stored punches in Django Admin and, where needed, correct them, without a console. This **changes** earlier rules: ?9 ("local edit or delete of punches" and "editing or deleting punches from the admin" out of scope) is lifted **only** as written below. UNIS stays the source of truth and is never written.

**Owner decisions (2026-10-15):** view and edit selected fields, audited; no delete; edits must not change counts; permissions `view_punches` and `edit_punches`; EID and RFID visible only with `view_punches`; every edit audited with old and new value.

**Owner decision on editable fields (2026-10-15, final):** **date, time, rfid and geolocation are editable. office, eid and terminal are read-only.** This supersedes the earlier 'key edits are refused': date and time are part of the unique key (office, eid, date, time, terminal), so changing them moves the punch to another key. The safeguards below (AC-16.3, AC-16.6, AC-16.8, AC-16.9) make that safe.

### US-16 Raw punch data
- **AC-16.1:** A menu entry **Raw punches** (Attendance, after the numbered steps) lists punches with filters (office, date range, terminal), a search by EID, newest first, with keyset-style paging that stays fast on 50M+ rows. A date range is required (default: today) so no query scans the whole table.
- **AC-16.2:** Viewing needs the new permission `view_punches`. A user without it cannot see the menu, EID or RFID, and gets a refusal (403).
- **AC-16.3:** A detail page shows one punch; users with `edit_punches` can change **date, time, rfid and geolocation** only. office, eid and terminal are read-only and cannot be changed by a crafted POST (server-side check). Inputs are validated (a real date, a real time, length, no control characters).
- **AC-16.4:** No add and no delete anywhere. Bulk edit and bulk actions do not exist.
- **AC-16.5:** Every edit writes an audit record with who, when, the punch key, the field and the old and new value. This audit is a separate table (`PunchEditLog`), because the operations audit holds no personal data. It is visible only with `view_punches`, is read-only and is **kept permanently** (not purged by housekeeping), because the original key of a moved punch is what stops sync from re-inserting it (AC-16.8). _Corrected during implementation from 'kept as long as the audit retention'; flagged to the owner._
- **AC-16.6:** An edit never creates or removes a punch: the total number of punches is unchanged. Changing the date moves one punch from one day to another, so the stored per-day counts of those two days change by one. Reconciliation records already stored are not rewritten; the next reconciliation of an affected day shows the difference, and the reconciliation page shows, for every day, how many punches were edited into or out of it (from the edit log), so a mismatch caused by an edit is recognisable. An edited punch is marked as edited on its detail page.
- **AC-16.8 (re-sync protection):** After a punch was edited to another date or time, a later forward sync or backfill must not bring back the original UNIS punch as a duplicate. The sync write path skips any punch whose original key is recorded in the edit log. An edit of only rfid or geolocation is never overwritten by a later sync.
- **AC-16.9 (collisions):** A date or time change is refused if a punch with the new key (same office, eid, terminal, new date and time) already exists, and is applied atomically (the move and the log row succeed or fail together). Moving a punch to a day or month without a partition is refused with a clear message.
- **AC-16.7:** `attendance.public` and the module boundary are unchanged; the admin reads the table through the module's own code only (AC-4.3 boundary test still passes). `list_punches` returns edited values.
- **Out of scope:** creating or deleting punches, editing office, eid or terminal, CSV export, editing UNIS, bulk edit.

## 4. Operations Clients Need
| Operation | Who may perform it | Related AC |
|---|---|---|
| Backfill an office/date range | Operator (command line) | AC-1.x |
| Run forward sync (scheduled) | System | AC-2.x |
| List punches | Other modules, in-process | AC-4.1 |
| Read sync status and reconciliation | Other modules, in-process | AC-4.1, 5.x |
| View and change attendance schedules (A-1) | Admin with `manage_schedule` permission | AC-7.x |
| View task results and run history (A-1) | Admin with `view_attendance` permission (Django view permission) | AC-7.4, 8.4 |
| Trigger a sync, test a UNIS connection (A-1) | Admin with `trigger_sync` permission | AC-8.1, 8.2, 11.3 |
| Retry a failed run (A-1) | Admin with `retry_runs` permission | AC-8.3 |
| Request, resume or cancel a backfill (A-1) | Admin with `manage_backfill` permission; over 31 days also `manage_large_backfill` | AC-9.x |
| View reconciliation and operations health (A-1) | Admin with `view_health` permission | AC-10.x, 11.x |
| Start, stop and supervise the background processes (A-1) | Operator (documented commands and auto-start) | AC-12.x |

Who may see attendance data as an end user: **OPEN**, out of scope until an API/UI feature. Which Django groups receive the permissions above is the owner's decision; this feature only defines the permissions (A-1).

## 5. Data and Ownership (business level)
- Owned only by `attendance`. EID is a plain reference (no link to an employee module yet; D-31 OPEN).
- Data: punches (50M+ rows expected), sync progress, sync runs, reconciliation records.
- **(A-1) Operational records, also owned only by `attendance`:** backfill jobs, task execution records, heartbeat evidence and an audit log of manual actions. They hold counts, dates, office codes, statuses, error kinds and the acting user, never punch data or secrets. Retention is a setting (OQ-A3).
- Sensitivity: personal attendance data and RFID card numbers. No exposure outside the interface.
- Volume: monthly partitioning by date is the intended design; detail goes to the plan. Retention: **OPEN**.

## 6. External Systems and Dependencies
- UNIS (3 servers, read-only, MSSQL; RAOWA uses a different database name). Reached only through a backend adapter (P4).
- **New dependencies/infrastructure needing explicit approval at plan stage (P7, D-40):** Celery, django-celery-beat, Redis (native on Windows, no Docker/WSL), and an MSSQL driver (recommendation `mssql-python`, fallback `pyodbc`; Python 3.14.5 compatibility to be verified in the plan).
- Depends on the existing Django/PostgreSQL foundation only.
- **(A-1) No new package is planned.** Task results are recorded by the module itself instead of adding `django-celery-results`. Auto-start uses the operating system's own facilities and a small supervisor in the repository; a third-party Windows service wrapper (NSSM or WinSW) would be a new tool and needs separate approval (OQ-A4). Redis on Windows remains an unofficial portable build in development (OQ-A6).

## 7. Non-Functional Requirements
- Performance: a 5-minute run per office finishes well inside 5 minutes; backfill is throttled so UNIS is not overloaded. Numeric targets **OPEN** (D-29/D-30).
- Security: read-only UNIS login; secrets from environment; no personal data in logs (P5).
- Auditability: run records (AC-5.1). Specific audit events **OPEN** (D-30). **(A-1)** Manual operations are audited (AC-13.3); the full list of security audit events stays OPEN.
- **(A-1) Safety:** admin actions respond immediately and never wait for UNIS or for a long task; health checks are time-limited; a backfill needs an explicit submit and a confirmation for long ranges; the UNIS connection test is a harmless read.
- Reliability: failures are recorded, existing data kept, the next run continues from the same point.

## 8. Edge Cases & Error States
UNIS unreachable or slow; a run overlapping the next; same-second punches at different terminals (kept, terminal is in the key); same person, time and terminal (one row); empty day; empty RFID; Redis or worker down (no data loss, catch-up on next run); time-zone mistakes. **(A-1)** Two administrators trigger the same office at once; a backfill request overlapping a running job; a worker busy with a long task not answering a health ping; Redis down while an admin presses "sync now" (the page says it could not queue the job and records nothing as queued); a job cancelled while a day is in progress; a retry of a run that has since been superseded; an administrator without the needed permission opening a link directly; the supervisor stopped while jobs are queued (they run when it returns).

## 9. Out of Scope
Late or edited UNIS rows; HTTP API; end-user UI pages (the Django Admin pages of A-1 are in scope); geolocation values; employee (ORBIS) linking; shift/daily attendance calculation; local edit or delete of punches; provisioning or operating a production server (documented service definitions are in scope, applying them is not); AI. **(A-1)** Also out of scope: starting the 2019-to-today backfill automatically, editing or deleting punches from the admin, a Next.js operations screen, alerts by email or chat, and adding `django-celery-results`.

## 10. Open Questions
- **OQ-1 (PROPOSED):** The unique key includes terminal (owner said "yes"; confirm in plan).
- **OQ-2 (DEFERRED):** Retention period for punches.
- **OQ-3 (DEFERRED):** Who may read attendance later (permissions), to the API feature.
- **OQ-4 (OPEN, for plan):** Backfill throttle limits, and the forward-sync starting point per office (end of backfill, or "now").
- **OQ-5 (OPEN, D-22):** Module structure as proposed in the plan notes; the plan proposes it for approval.
- **OQ-6 (OPEN, for plan):** Approval of each new dependency and Redis (P7).

**Open questions added by Amendment A-1 (resolved 2026-10-15: the owner accepted all proposed defaults below; OQ-A8 is an owner-side step):**
- **OQ-A1 (limits):** Per-request backfill span limit 366 days, and an extra confirmation plus the large-backfill permission above 31 days.
- **OQ-A2 (generic Beat admin):** The standard django-celery-beat admin pages (which can create any task) stay available to superusers only; attendance administrators use the attendance schedule page.
- **OQ-A3 (retention):** Task execution records kept 30 days, heartbeat evidence 2 days, the audit log 365 days; all configurable.
- **OQ-A4 (Windows auto-start):** A per-user "at sign-in" scheduled task that starts the supervisor (no administrator rights; runs only while the user is signed in) is the default. A Windows service through NSSM or WinSW (always on, needs administrator rights and a new tool) is the alternative.
- **OQ-A5 (production):** Linux with systemd units as the reference production setup; the actual hosting stays OPEN (Constitution §3).
- **OQ-A6 (Redis on Windows):** Keep the unofficial portable Redis 5 build for development, or move to Memurai (administrator rights and a licence for production use).
- **OQ-A7 (task results):** Record task results in the module's own tables instead of adding `django-celery-results`.
- **OQ-A8 (roles):** Which Django groups get which of the six new permissions (the owner assigns them; no role is invented here).

## 11. Change Log
| Date | Change | Reason | Approved by |
|---|---|---|---|
| 2026-10-15 | **Amendment A-1 (PROPOSED):** added US-7 to US-13, AC-7.x to AC-13.x (§3a), operations in §4, operational records in §5, no new package in §6, safety in §7, extra edge cases in §8, admin pages in scope in §9, OQ-A1 to OQ-A8 in §10 | Owner wants to manage scheduling, sync, backfill and monitoring from Django Admin and have the background processes start reliably | Project owner, 2026-10-15 (`approved`; scope: spec A-1, plan §13a, tasks T24–T42; all proposed defaults accepted) |
| 2026-10-15 | **Amendment A-2 (APPROVED):** added US-14 / AC-14.x (?3b): first-time setup page in Django Admin | Owner wants setup without the command line | Project owner, 2026-10-15 |
| 2026-10-15 | **Amendment A-3 (APPROVED):** added AC-15.x (?3c): step-ordered menu, module README | Owner request | Project owner, 2026-10-15 |
| 2026-10-15 | **Amendment A-4 (APPROVED):** added AC-16.x (?3d): raw punch menu with audited edit of rfid and geolocation; lifts the A-1 'no editing from the admin' rule in that scope only; date and time editable by owner decision | Owner request | Project owner, 2026-10-15 |
---
**Status:** Approved (US-1 to US-6, 2026-10-14; Amendments A-1, A-2, A-3 and A-4, 2026-10-15) · **Approved by:** Project owner (`SPEC APPROVED` 2026-10-14; A-1 and A-2 approval 2026-10-15) · **Date:** 2026-10-15 · **Linked constitution:** `docs/constitution.md` (v1.1)
