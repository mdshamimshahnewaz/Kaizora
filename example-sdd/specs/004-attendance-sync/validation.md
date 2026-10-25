# Validation Record — Attendance Sync

> **Purpose:** prove each acceptance criterion in `spec.md` is met. A requirement is **Passed** only when its test or validation was actually executed and the result recorded (Constitution P6). Planned and executed validation are reported separately.
> **Location:** `specs/004-attendance-sync/validation.md`.
> **Important:** the first sections were written before any real UNIS access. Real UNIS checks for MHK and RAOWA were executed on 2026-10-14; **MBD became reachable on 2026-10-15 and was checked then** (see §2a). Redis, real Celery workers (`--pool=solo`) and Celery Beat were run on this Windows machine. Rows marked Passed without a "real" note were executed against fakes, a mocked driver or the local PostgreSQL test database. Amendment A-1 (admin-managed operations) is validated in §2a.

## 1. Planned Validation
| Spec ID | Planned test / check |
|---|---|
| AC-1.1–1.3 | `test_use_cases.BackfillTests`, `test_tasks_commands` (backfill command, task, month chunks); manual T22 (real day, resume) |
| AC-2.1–2.3 | `test_use_cases.ForwardSyncTests`, `test_tasks_commands.TaskTests`, `test_persistence.OfficeLockTests`; manual T22 (5-minute cycles on Windows) |
| AC-3.1–3.3 | `test_persistence.PunchRepositoryTests`, `OfficeLockTests`, `ForwardSyncTests`/`BackfillTests` rollback tests |
| AC-4.1–4.3 | `test_public`, `test_boundary` |
| AC-5.1–5.3 | `test_persistence.ProgressRepositoryTests`, `test_public` (status, reconciliation), admin registration; manual T22 (forced mismatch) |
| AC-6.1, 6.2 | `test_unis_adapter` (query text, read-only, secret leakage), `test_boundary.test_unis_vocabulary_stays_inside_the_adapter` |
| AC-D.1–D.3 | `test_unis_adapter.MappingTests`, `test_persistence`, `test_use_cases`; manual T22 (real column types) |
| Spec §7 performance | T21 synthetic load; manual T22 |

## 2. Executed Validation
Date: 2026-10-14. Windows, local PostgreSQL, Python 3.14.5, Django 6.1.2, celery 5.6.3, django-celery-beat 2.9.0, mssql-python 1.16.0.

Commands run:
- `manage.py check` → no issues. `manage.py makemigrations --check --dry-run` → no changes.
- `manage.py test attendance accounts about core --noinput` → **161 tests, OK** (attendance's own tests are the new ones; `accounts`, `about`, `core` still pass).
- Compatibility check (T1): `check`, `makemigrations --check`, `core` tests and saving a `PeriodicTask` with `django_celery_beat` in a temporary settings module on Django 6.1.2 → all fine. `pip check` still reports the declared `Django<6.1` constraint of `django-celery-beat` (decision D-62).
- Eager Celery: `forward_sync_all.apply()` and `ensure_partitions_task.apply()` ran through Celery's eager mode in tests; the Celery app and the three task names, routes, JSON serializer and `DatabaseScheduler` were loaded and printed.
- T21 synthetic load (temporary test database, removed afterwards): 6,000,000 synthetic rows seeded in 318.5 s (SQL `generate_series`, not the application path).

**Real Redis and Celery run (T22, partial), 2026-10-14:**
- Redis: no admin rights, so Memurai (needs a Windows service) was not installed. A portable, unofficial Windows build (tporadowski/redis 5.0.14.1, from its GitHub release, no checksum published) was unzipped to `%LOCALAPPDATA%\Redis` and started on `127.0.0.1:6379` (`PONG`). It is still running.
- Finding: `redis` client 8.1.0 (pinned in the plan) speaks RESP3 (`HELLO 3`) and failed against Redis 5; it is also outside `kombu`'s supported range (`redis<6.5`). Corrected to `redis==6.4.0` (same approved package, supported version). Plan change log updated.
- With `redis` 6.4.0: a real `celery -A config.celery worker --pool=solo -Q attendance_sync` connected and ran `forward_sync_all` and `ensure_partitions` sent through the broker (both succeeded). With no UNIS values configured, each office recorded `failed / not_configured` without crashing the task, and the other offices continued (AC-2.2, AC-6.2 in a real worker).
- A real `celery beat` (django-celery-beat `DatabaseScheduler`) sent `attendance forward sync` about 5 minutes after start; the worker ran it and 3 more run records appeared (6 in total). The test run records and error markers were deleted afterwards. Beat schedule entries and forward-sync cursors (today 00:00) remain in the dev database.
- Not observed: several consecutive cycles, the `attendance_backfill` worker, Redis stopped mid-run, UNIS stopped mid-run.

**Real UNIS checks (T22, partial), 2026-10-14 evening.** Credentials come from `backend\.env`; only aggregate numbers, column types and statuses are recorded here. No EID, RFID, employee data, host, user name, password or connection string was printed or written. UNIS was only read (SELECT); nothing in UNIS was modified.
- **Driver:** `mssql-python` 1.16.0 imports and connects on Python 3.14.5 (AMD64); no second driver (`pyodbc`, `pymssql`) is installed. Against a closed local port the real driver raised `mssql_python.exceptions.OperationalError`, and the adapter turned it into `SourceUnavailable` with no chained exception.
- **Variable names:** the adapter, settings and `.env.example` agree on all 12 per-office names plus `REDIS_URL` and the sync settings (three optional tuning names were added to `.env.example`). All 12 required values are filled in `.env` (checked as set/empty only).
- **Connectivity:**
  | Office | Result |
  |---|---|
  | MHK | TCP reachable. Connect with the default `Encrypt=yes` fails: "certificate chain was issued by an authority that is not trusted" (self-signed server certificate). Connects with `TrustServerCertificate=yes`. |
  | RAOWA | Same as MHK. |
  | MBD | **Not reachable on 2026-10-14:** TCP connection to the configured host and port timed out (non-default port). **Update 2026-10-15: reachable and fully checked, see §2a.** |
  The MHK and RAOWA checks below were run with `UNIS_TRUST_SERVER_CERTIFICATE=True` set for that process only; `.env` was not changed. Whether to accept that setting permanently, or to install the UNIS certificate authority on this machine, is an owner decision.
- **Rights:** for MHK and RAOWA the login is not `db_owner`, not `db_datawriter` and not `sysadmin` (role-membership check only; explicit table grants were not enumerated).
- **Column types (confirms the plan's assumption):** `tEnter.C_Date` and `C_Time` are fixed-width text (MHK `char(8)`/`char(6)`, RAOWA `nvarchar(8)`/`nvarchar(6)`); `L_UID` and `L_TID` are `int`; `C_Card` is `varchar(24)`/`nvarchar(24)`; `tTerminal.C_Name` is `varchar(30)`/`nvarchar(30)`; `tTerminal.L_ID` is `int`. `tEnter.C_Date` ranges: MHK 20190101 to 20261014, RAOWA 20231216 to 20261014.
- **Sample day 2026-10-13 through the adapter (in memory first):**
  | Office | Rows mapped | Skipped malformed | Distinct keys | Duplicates | Employees | Terminals | Empty RFID | RFID with a leading zero | Longest eid / terminal / rfid |
  |---|---|---|---|---|---|---|---|---|---|
  | MHK | 5,973 | 0 | 5,973 | 0 | 357 | 18 | 62 | 4,268 | 7 / 17 / 8 |
  | RAOWA | 2,189 | 0 | 2,189 | 0 | 329 | 3 | 12 | 1,673 | 5 / 15 / 8 |
  Both fit the stored column sizes (eid 64, terminal 255, rfid 64) and leading zeros survive.
- **One-day backfill (2026-10-13) into the local database, MHK and RAOWA only:** 5,973 and 2,189 rows inserted. A second run read nothing (`1 skipped`, 0 inserted). Reconciliation: MHK `unis_count 5973 / local_count 5973`, RAOWA `2189 / 2189`, both not a mismatch. Default partition rows: 0.
- **Real forward sync (cursor started at today 00:00):** first run MHK 5,464 and RAOWA 1,683 rows read and inserted for 2026-10-14; second run re-read 1 row (the inclusive cursor second) and inserted 0. Reconciliation for 2026-10-14 also equal (5,464 / 1,683). `public.get_sync_status()` and `public.list_punches()` returned live data (a 1,000-row page with a next-page cursor).
- **Mismatch drill (non-destructive):** reconciling MHK 2026-10-12, a day never loaded locally, gave `unis_count 5403 / local_count 0`, flagged as a mismatch and logged, and nothing was auto-fixed. The drill row was then deleted from the local reconciliation table.
- Not executed on 2026-10-14 (MBD, a Celery-driven forward cycle and stopping UNIS or Redis were later done or simulated, see §2a): the multi-year backfill. No full historical backfill was started.

| Spec ID | Test (file / name) | Result | Evidence / notes |
|---|---|---|---|
| AC-1.1 | `BackfillTests.test_loads_every_day_in_the_range_oldest_first`; `TaskTests.test_backfill_task_loads_days…`; `CommandTests.test_backfill_command_runs_inline…` | Passed (fakes + real PostgreSQL; MHK and RAOWA one-day backfill against real UNIS, 2026-10-13) | MBD not reachable; no multi-year run. |
| AC-1.2 | `BackfillTests.test_resumes_at_the_first_unfinished_day`, `test_rerunning_a_finished_range_reads_nothing`; `CommandTests.test_backfill_command_reports_a_failed_day_and_can_resume` | Passed | |
| AC-1.3 | `BackfillTests.test_limited_to_one_office_by_the_caller`; command `--office/--from/--to` tests; `test_month_chunks…`, `test_enqueue_backfill…` | Passed | |
| AC-2.1 | `ForwardSyncTests` (first run, inclusive cursor second, catch-up over several days); `TaskTests.test_forward_task_runs_eagerly…` | Passed | Cursor handling tested with fakes; the 5-minute beat firing was not observed (needs Redis). |
| AC-2.2 | `test_one_office_failing_does_not_stop_the_others`, `test_an_unexpected_crash_in_one_office_is_isolated`, `TaskTests.test_one_failing_office…` | Passed | |
| AC-2.3 | `test_a_busy_office_is_skipped`, `OfficeLockTests` (second PostgreSQL session cannot take a held lock; released after use and after an exception) | Passed | |
| AC-3.1 | `PunchRepositoryTests` (idempotent insert, in-batch duplicates, same second at two terminals, two offices) | Passed (real PostgreSQL) | |
| AC-3.2 | `test_insert_failure_rolls_back_the_batch_and_the_cursor`, `PunchRepositoryTests.test_a_failed_batch_stores_nothing`, `test_a_failed_insert_rolls_back_the_day`, `test_a_failed_day_stores_nothing…` | Passed | |
| AC-3.3 | `OfficeLockTests`; backfill/forward both take the same per-office lock; `test_a_busy_office_stops_without_marking_anything` | Passed | Lock is per office (stricter than per day). |
| AC-4.1 | `test_public` (paging, filters, validation, status, reconciliation) | Passed | |
| AC-4.2 | `test_public.test_returns_plain_frozen_objects` | Passed | |
| AC-4.3 | `test_boundary` (4 rules and a deliberate-violation check) | Passed | Checker proved to fail on a violation in a temp file. |
| AC-5.1 | `ProgressRepositoryTests.test_run_records_hold_counts_and_a_kind_only`; use-case tests asserting run records | Passed | |
| AC-5.2 | `ReconcileTests`, `ForwardSyncTests.test_reconciliation_runs…`, `BackfillTests` | Passed (fakes); Partial (real UNIS) | Real MHK and RAOWA counts matched for 2026-10-13 and 2026-10-14 and a non-destructive drill flagged an unloaded day. MBD not checked; a drill that deletes loaded rows was deliberately not run. |
| AC-5.3 | `test_public.test_sync_status_lists_every_configured_office`; read-only admin registered | Partial | Admin pages were not opened in a browser. |
| AC-6.1 | `test_unis_adapter.QueryTests` (parameterised SELECT only, no write keywords), `test_boundary` vocabulary test | Passed | |
| AC-6.2 | `test_unis_adapter.ErrorTests`, `ConfigTests` (no host, user or password in exception text, repr or traceback; config repr hides secrets); `TaskTests.test_task_results_carry_counts_and_kinds_only` | Passed | Verified for the adapter and the sync path with fake drivers. |
| AC-D.1 | `MappingTests`, `PunchRepositoryTests.test_rfid_leading_zeros_and_null_are_kept`, `PartitionTests` | Passed | Real column types confirmed for MHK and RAOWA (§2). MBD unconfirmed. |
| AC-D.2 | `LocalClock` uses Asia/Dhaka; no UTC conversion in mapping or storage | Partial | Code review plus mapping tests; the clock in a real deployment was not observed. |
| AC-D.3 | Office comes from the configured UNIS server in every use case test | Passed | |

## 2a. Amendment A-1 (admin-managed operations, health, supervised startup): planned and executed validation
> A-1 implemented 2026-10-15 under the owner's `implement` instruction. Planned and executed results are kept apart. Evidence from the browser-visual review by the owner is **not** included: it has not happened yet.

### Planned (spec §3a, plan §13a.11)
| Spec ID | Planned test / check |
|---|---|
| AC-7.1–7.3 | `test_admin_operations.ScheduleAdminTests`, `PermissionMatrixTests`; real page check |
| AC-7.4 | `test_ops_tasks.TaskEventTests`, `HousekeepingTests`; real worker run |
| AC-8.1–8.4 | `test_operations` (Trigger, Retry), `test_admin_operations.SyncOperationsTests`, `test_ops_store`; real admin action and outage drill |
| AC-9.1–9.7 | `test_operations.BackfillRequestTests`, `ResumeCancelTests`, `test_admin_operations.BackfillFormTests`, `test_ops_tasks.BackfillJobLifecycleTests`, `test_ops_store.ConcurrentRequestTests`; real one-day job |
| AC-10.1–10.3 | `test_admin_operations.ReconciliationPageTests`; real reconciliation |
| AC-11.1–11.4 | `test_health` (every basis label, no-reply wording, timeouts), `test_admin_operations.HealthPageTests` (secret scan); real health page and outage drills |
| AC-12.1–12.4 | `test_supervisor` (fakes and small real child processes), `test_broker`; real supervisor run and Windows task |
| AC-13.1–13.4 | `test_admin_operations.PermissionMatrixTests` (anonymous, no permission, each permission, superuser; POST-only; CSRF), `test_operations` (validation table), audit assertions everywhere, `test_boundary`, `test_ops_store.PublicInterfaceUnchangedTests` |

### Executed: automated
Date 2026-10-15. `manage.py test attendance accounts about core --noinput` → **290 tests, OK** (the 161 earlier tests still pass; 129 new). `manage.py check` clean. `makemigrations --check` clean. Migration `0003_operations` applied to the development database.

### Executed: real systems (development machine, Windows, real Redis 5 portable build, real Celery workers, real UNIS)
No credentials, hosts, EIDs or RFIDs were printed. A temporary superuser was used for the admin checks and deleted afterwards. The admin pages were requested with Django's test client against the development database (real templates, real data, real broker and workers); **they were not opened in a browser**.
| Check | Result |
|---|---|
| Windows auto-start | `scripts\windows\attendance-service.ps1 install` registered the per-user at-sign-in task **without administrator rights**; `start` ran it through Task Scheduler; the supervisor came up with sync worker, backfill worker and Beat. |
| Crash recovery | Killing the sync worker process: the supervisor restarted it within seconds (restart count 1). Killing the backfill worker: restarted (count 2); the health page showed "No worker listens on attendance_backfill" until it re-registered, which took longer than 10 s (it was fully back about two minutes later). |
| Clean stop | `run_attendance_services --stop` stopped the three processes in about 25 s and removed the pid file; `--status` then reported "not running". |
| Health page (real) | Database ok [live]; Broker PING ok [live]; Workers: 2 replied with both queues [live]; Beat ok [observed] after the heartbeat job was created and Beat dispatched it; Worker consumption ok [observed]; Supervisor ok [observed]; schedule rows [inferred]. First page load after a fresh start took about 4 s (celery app and first control call), later loads about 0.1 s. |
| Sync now from admin (MHK) | "Sync queued"; a second press at once: "A sync for this office is already queued"; the real worker finished it (`success`, started by the admin user, 25 rows read, 24 inserted). Audit rows written for both. |
| Backfill form (MHK, 2026-10-12, one day) | Job queued and finished by the real worker: `done`, 1/1 days, 5,403 rows; an overlapping second request was refused ("An active backfill for this office already covers some of these dates"). The day that earlier showed a mismatch (5403 vs 0) now reconciles 5403 / 5403. Audit rows: requested/queued, requested/refused (overlap). |
| Scheduled forward sync via Beat, real UNIS | Beat dispatched `attendance.forward_sync_all` and the worker ran it: MBD, MHK and RAOWA all `ok` (for example 9, 62 and 10 rows in one cycle), recorded as `scheduled`; cursors advanced to the current time; heartbeats recorded (8 by then). |
| Redis stopped | Health: Broker DOWN [live] (`OperationalError`), Workers UNKNOWN "Not checked: the broker is unavailable", Beat and consumption still Observed. "Sync now" answered "Could not queue the sync: the broker is unavailable", left no queued marker and wrote an audit row `failed / broker_unavailable`. Timing on Windows: the action answered in about 6 s before tuning and about 2 s after (a refused loopback connection costs the OS about 2 s per attempt); the health page takes about 6 s while Redis is down. |
| Redis restarted | The workers reconnected by themselves; heartbeats resumed (2 finished in the next 100 s); about two minutes later every status was ok again. |
| MBD (real UNIS), first time reachable | Connected; login is not `db_owner`, `db_datawriter` or `sysadmin`; column types identical to MHK (`char(8)` date, `char(6)` time, `int` ids, `varchar(24)` card, `varchar(30)` terminal name); `tEnter` dates 20240801 to 20261015. Sample day 2026-10-13: 1,884 rows mapped, 0 malformed, 0 duplicates, 214 employees, 5 terminals, 15 empty RFID, 1,248 RFID with a leading zero. One-day backfill: 1,884 rows inserted; reconciliation source 1884 / local 1884. |
| Reconciliation, all offices | MBD 2026-10-13 and 2026-10-15, MHK 2026-10-12 to 2026-10-15, RAOWA 2026-10-13 to 2026-10-15: every row matches (no mismatch). |
| Task restored | After the checks the scheduled task was **uninstalled** and the services stopped, so nothing runs in the background now. |

### Acceptance criteria (A-1)
| Spec ID | Result | Evidence / notes |
|---|---|---|
| AC-7.1 | Passed (automated); Partial (visual) | Page lists only attendance jobs with last run, total runs, estimated next run labelled "(estimated)". Not viewed in a browser. |
| AC-7.2 | Passed (automated) | Enabled and interval 1 to 60 min change, audited; Beat's database scheduler picks a change up without restart by design. Not observed live (the job's new interval was not watched for two cycles). |
| AC-7.3 | Passed | Unknown tasks unreachable, no add, no delete, fixed jobs have no interval field, generic Beat admin is superuser-only. |
| AC-7.4 | Passed | Task executions for scheduled and manual runs recorded with state, times, counts, error kind; no personal data (whitelist test). Retention is a setting; pruning tested with fake data. |
| AC-8.1 | Passed | Real worker run from admin; the action returns at once. |
| AC-8.2 | Passed | Real duplicate refused; stale queued marker expires; lock-held case tested with a second PostgreSQL session. |
| AC-8.3 | Passed (automated) | Retry rules tested (failed, latest, no active run; forward and backfill; idempotent). Not exercised with a real failed run. |
| AC-8.4 | Passed | Run history shows who started it, retry link, counts, error kind. |
| AC-9.1 | Passed | Validation table tested (office, dates, future, before start, span, 31 days). |
| AC-9.2 | Passed | One real job queued through the form; nothing creates a job elsewhere (tested across all pages, migrations and the schedule setup). |
| AC-9.3 | Passed | Overlap refused, real and in a two-thread race. |
| AC-9.4 | Passed | State, progress `days_done/days_total`, rows, failed day and error kind updated by the worker (real one-day job; lifecycle tests for the rest). |
| AC-9.5 | Passed (automated) | Resume from the failed day or after processed days; cancel of a queued job and a cooperative cancel mid-run. A real mid-run cancel with a worker was not executed. |
| AC-9.6 | Passed | Re-check mode re-reads a loaded day (idempotent). The reconciliation link opens the prefilled form. |
| AC-9.7 | Passed | Over 31 days needs confirmation and permission; cap 366. |
| AC-10.1–10.3 | Passed (automated + real data); Partial (visual) | List, filters, difference, summary page, no edit or fix action. |
| AC-11.1, 11.2 | Passed | Every status has a basis label and a time; no bare "OK". |
| AC-11.3 | Passed | Broker and workers live; Beat observed from the heartbeat dispatch; UNIS test button live and audited (unit-tested; the button was not pressed on the real page). "No reply (a long task may be running)" tested; a real silent solo worker during a long backfill was not observed. |
| AC-11.4 | Passed | Timeouts tested; page never raised during the outage drills; secret scan of the page against the real `UNIS_*` values and `redis://`. |
| AC-12.1 | Passed | Supervisor starts and restarts the three processes, writes logs and a status file, single-instance guard (real). Starting Redis itself (`REDIS_SERVER_PATH`) was tested with fakes only. |
| AC-12.2 | Partial | Installed and started without administrator rights and the commands exist (real). Not observed across a real sign-out/sign-in or a restart. |
| AC-12.3 | Partial | systemd units and the Windows-service outline written as templates. Not applied or tested on any server; the units have not been run through `systemd-analyze`. |
| AC-12.4 | Not executed | Needs a real sign-out/sign-in (or restart) cycle on the machine; only the equivalent "run task now" path was exercised. |
| AC-13.1 | Passed | Permission matrix across all pages and actions; POST-only; CSRF enforced. |
| AC-13.2 | Passed | Office list, dates and ids validated on the server; no free-text tasks. |
| AC-13.3 | Passed | Audit rows for queued, refused and failed operations, schedule changes and connection tests. |
| AC-13.4 | Passed | `attendance.public` exports exactly the approved names; boundary test passes. |

### Implementation notes for review (A-1)
- `TaskEvent` also has an `office` field (the plan sketch did not list it); the duplicate guard needs it.
- `django_celery_beat` now precedes `attendance` in `INSTALLED_APPS` so its admin is registered first and can be restricted to superusers.
- The default `REDIS_URL` is `redis://127.0.0.1:6379/0`; health and "queue a task" requests also turn `localhost` into `127.0.0.1` (Windows IPv6 delay). Your `backend\.env` still says `localhost` for the workers; changing it to `127.0.0.1` is recommended.
- `setup_attendance_schedule` no longer overwrites an interval or on/off state you changed in Admin.
- `backend/logs/` is ignored in `.gitignore`.
- A cleanup of a mangled plan footer (an earlier edit) was done along with the A-1 amendment.

## 2b. Amendment A-2 (setup page in Django Admin; spec, plan, tasks, implementation and this validation approved by the owner 2026-10-15)
| AC | Check | Result | Evidence |
|---|---|---|---|
| AC-14.1 | Three steps with status, evidence, help text and overall line | Passed (automated + rendered page on the dev DB) | `attendance.tests.test_setup_page`; real GET returned 200 with all steps and "Setup incomplete" |
| AC-14.2 | Idempotent buttons; schedule keeps admin changes; start points never overwrite; partitions only create missing | Passed (automated) | `SetupServiceTests` |
| AC-14.3 | `manage_schedule` required, POST-only actions, server validation | Passed (automated) | `SetupAdminTests` (403 without permission, bad office/date refused) |
| AC-14.4 | Audit record per press | Passed (automated) | `test_buttons_do_the_work_and_audit`, `test_bad_input_refused_and_audited` |
| AC-14.5 | Commands unchanged; boundary intact | Passed | 303 tests pass (`attendance accounts about core`), `makemigrations --check` clean |
| Not executed | Owner's browser use of the page and pressing the real buttons on the dev DB (left for the owner; the attendance data was wiped on 2026-10-15 at the owner's request, so the page shows "Needs action") | Not executed | — |

Status: **Approved** by the project owner on 2026-10-15 (the browser use of the real buttons stays with the owner).

## 2c. Amendment A-3 (step-ordered menu, module README)
| AC | Check | Result | Evidence |
|---|---|---|---|
| AC-15.1 | Attendance menu numbered and ordered; other apps unchanged | Passed (automated) | `tests/test_menu_order.py`; `manage.py check` clean |
| AC-15.2 | Module README exists | Passed (file review) | `backend/attendance/README.md` |
| Not executed | Owner's look at the menu in the browser | Not executed | - |

Status: **Approved** by the project owner on 2026-10-15 (the browser look at the menu stays with the owner).

## 2d. Amendment A-4 (raw punch menu with audited edit)
| AC | Check | Result | Evidence |
|---|---|---|---|
| AC-16.1 | List with required date range (default today), office/terminal filters, exact EID search, paging; range and date validation | Passed (automated + real GET on the dev DB) | `test_punch_edit.RawPunchAdminTests`; the real list page returned 200 with 100 rows and edit links |
| AC-16.2 | `view_punches` needed for menu, list and detail; others refused (403), anonymous redirected | Passed (automated) | `test_permissions`, `test_viewer_sees_but_cannot_edit` |
| AC-16.3 | Only date, time, rfid and geolocation editable; a crafted POST changing office, eid or terminal refused; input validated | Passed (automated) | `test_crafted_post_cannot_change_key_fields`, `test_bad_input_refused`, `PunchEditorTests` |
| AC-16.4 | No add, no delete, no bulk action | Passed (automated) | `test_no_add_delete_and_log_is_read_only` |
| AC-16.5 | Every edit logged with who, when, key, old and new values; log read-only, `view_punches` only, never purged | Passed (automated) | `test_editor_changes_date_time_rfid_geolocation_and_logs`, `test_no_add_delete_and_log_is_read_only` |
| AC-16.6 | Total unchanged; per-day counts move by one; reconciliation page shows edited in/out; stored rows not rewritten | Passed (automated) | `test_move_to_other_date_and_time`, `test_reconciliation_shows_edited_in_out` |
| AC-16.7 | `attendance.public` and boundary unchanged | Passed | boundary test and the full suite (324 tests) pass; `makemigrations --check` clean |
| AC-16.8 | Sync and backfill do not bring back a moved punch; rfid edit not overwritten; others still inserted | Passed (automated) | `test_resync_*`, `test_other_punches_still_inserted` |
| AC-16.9 | Collision, date outside range and missing partition refused, atomic | Passed (automated) | `test_collision_refused`, `test_date_range_and_partition_refused` |
| Not executed | An edit in the browser on real data; a real re-sync after an edit against UNIS; behaviour of the page on tens of millions of rows (the date range keeps queries on one or a few partitions; no timing measured) | Not executed | - |

Follow-up 2026-10-15 (owner request, presentation only, no scope change): the Raw punches list now uses Django's own changelist layout (toolbar with the office, date range, terminal and EID filters, `result_list` table with the date as the link, striped rows, Django-style numbered paginator with a total capped at 100,000). Checked by `test_list_uses_changelist_layout_with_paginator`, `test_pagination_pages` and a real GET on the dev DB. Not looked at in a browser by the agent. Approved by the project owner (`validate approved`) on 2026-10-15.

Notes: the edit log holds personal data (eid, rfid) by design. It is never purged because the sync guard depends on it. Migration 0005 is applied to the dev DB. No data was edited on the dev DB.

Status: **Approved** by the project owner on 2026-10-15 (the browser edit on real data and a real re-sync after an edit stay with the owner).

## 3. Non-Functional / Performance (T21, synthetic data only, no pass/fail target exists, D-29 OPEN)
Machine: this development PC, local PostgreSQL, 6,000,000 synthetic rows across monthly partitions (about 186,000 rows and 37 MB in one partition).

| Measurement | Result |
|---|---|
| Insert one office-day batch of 6,500 rows (temp table, COPY, `ON CONFLICT DO NOTHING`) | 0.32 s |
| Re-insert the same batch (all duplicates, 0 inserted) | 0.11 s |
| `count_day` for one office/day | 0.016 s |
| List 500 rows for 2 EIDs over three years (keyset) | 0.18 s |
| List 1,000 rows, one office, one month (keyset) | 0.12 s |
| Default partition rows after the load | 0 |
These are single runs on a warm development machine, not a benchmark. A real 50M+ table on production hardware, memory use with a 5,000-row fetch chunk, and UNIS load were Not measured.

## 4. API-First Compliance
| Check | Result | Evidence |
|---|---|---|
| Contract matches the plan | Passed | `public.py` functions, DTOs, limits (max 1000, 31-day span without EIDs) tested |
| No HTTP endpoint added | Passed | No URL, view or serializer in `attendance` |
| Frontend | Passed | No frontend change; no BFF handler |
| Authentication and permission cases | Not applicable | No HTTP surface; end-user read permissions deferred (OQ-3). Admin pages are read-only (no add/change/delete). |
| External systems only through adapters | Passed | UNIS only in `infrastructure/unis/adapter.py` |
| No module accesses another module's models or tables | Passed | `test_boundary` |

## 5. Constitution Compliance
| Principle | Result | Evidence |
|---|---|---|
| P1 Spec first, gates | Passed | Spec, plan, tasks approved 2026-10-14; implementation separately authorised |
| P2 Decisions labelled | Passed | D-59 to D-62 recorded with dates; deferred items listed in §6 |
| P3 Modular monolith | Passed | `attendance` module, interface-only access, boundary test |
| P4 Adapters | Passed | UNIS read-only through `PunchSource` |
| P5 Security, privacy, audit | Passed with limits | Secrets only from environment, no data in logs or run records (tested with fakes); run records. Real credentials/logs not inspected. |
| P6 Evidence-based validation | Passed | This record separates executed from not executed |
| P7 Minimal footprint | Passed | Only the four approved packages (plus their pinned dependencies) and a Redis requirement; no Docker/WSL; no AI |
| P8 API-first | Passed | No HTTP API yet; `public.py` is the contract a later API will wrap |

## 6. Outcome
Overall status: **Ready for the owner's review, with limitations (T22 mostly executed, A-1 implemented). Approved by the owner on 2026-10-15 with these limitations.** The attendance sync works against real UNIS for all three offices (MBD became reachable on 2026-10-15), reconciles, runs under a real Celery worker and Beat, and Amendment A-1's admin pages, health checks and supervisor were exercised against real Redis, workers and data.

Limitations and follow-ups:
- **Task T22 (real systems), what remains:** stopping a UNIS server **mid-run** was not done (only simulated with a failing source and a closed port); the **multi-year backfill** (2019 to today) was not started and needs the owner's explicit approval; the supervised services were run for about 10 minutes, not for days.
- **Task T41 (A-1 manual verification), what remains:** the owner's **browser** walkthrough of every admin page (layout, wording, usability); a real **sign-out / sign-in or restart** to see the auto-start task launch the services (AC-12.2, AC-12.4); a real **mid-run cancel** with a worker; pressing the "Test connection" button on the real health page; reviewing the systemd and Windows-service templates on a real server (AC-12.3).
- **Owner steps still open:** assign the six new permissions to Django groups (OQ-A8); change `REDIS_URL` in `backend\.env` from `localhost` to `127.0.0.1` for speed on Windows; decide when to turn the sign-in task on (`.\scripts\windows\attendance-service.ps1 install`); decide when and how to start the 2019 backfill (several confirmed jobs of at most 366 days per office).
- The background services and the sign-in task are **stopped and removed** now. The development database holds the one-day loads (MHK 2026-10-12 to 15, MBD 2026-10-13 and 15, RAOWA 2026-10-13 to 15) and about 15 minutes of scheduled sync.
- **TLS decision (closed 2026-10-14, D-63):** the owner set `UNIS_TRUST_SERVER_CERTIFICATE=True` for all offices in `backend\.env`, accepting that the UNIS server certificate is not validated. Re-checked with only the `.env` value (no per-process override): MHK and RAOWA connect and return the same counts for 2026-10-13 (5,973 and 2,189); MBD connected on 2026-10-15.
- The Redis used here is an unofficial portable Windows build of Redis 5.0.14 started by hand (not a service, gone after a reboot). For anything beyond development a supported Redis (Memurai needs admin rights, or Linux hosting) is still OPEN.
- `mssql-python` was only exercised through a mocked driver. The driver's connection-string options (`ApplicationIntent`, `Encrypt`, `TrustServerCertificate`) and `timeout` arguments are taken from its signature and ODBC conventions and need the real connection check.
- Celery 5.6.3 on Windows is not officially supported; a real `--pool=solo` worker and beat ran for one cycle only. `pip check` reports the `django-celery-beat` / Django 6.1 constraint (D-62).
- The 2019-to-today backfill is operated by the owner after sign-off and was not run.
- Not done on purpose (out of scope): HTTP API, UI, late/edited rows, geolocation values, retention (DEFERRED), end-user read permissions (DEFERRED).
- `DEFAULT` partition stays empty in tests; the daily `ensure_partitions` task keeps future months ready, but a missing-partition alert beyond a log warning does not exist.
- Collapsing rows: two real punches with identical (office, eid, date, time, terminal) become one row (accepted key choice). `unis_count` is a distinct count over the same fields, so such duplicates do not show as mismatches; rows the adapter skips as malformed would.
- No commit or push was made.

## 7. Change Log
| Date | Change | Reason | Approved by |
|---|---|---|---|
| — | — | — | — |

---
**Status:** Approved (with the recorded limitations: T22/T41 owner items and the historical backfill remain open) · **Approved by:** Project owner (`VALIDATION APPROVED`) · **Date:** 2026-10-15
