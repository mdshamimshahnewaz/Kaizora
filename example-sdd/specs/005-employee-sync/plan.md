# Technical Plan — Employee Sync

> **Purpose:** HOW the approved `spec.md` (with Amendment A-1) will be implemented. Every decision traces to a spec item.
> **Location:** `specs/005-employee-sync/plan.md`. **Rules:** `docs/constitution.md`, `docs/architecture.md`, `docs/api-conventions.md`.
> Status labels: CONFIRMED, PROPOSED, OPEN, DEFERRED. Items the owner must decide are collected in §8a.

## 1. Linked Spec
Source: `specs/005-employee-sync/spec.md` · Covers: US-1 to US-9, AC-1.1 to AC-9.6. Decisions relied on: D-59, D-61, D-62, D-64, D-65 (reused infrastructure), D-67 (encrypted token).

## 2. Architecture Overview
A new Django app `employee`, structured like `attendance` (D-61), one deployable, no new infrastructure:

```
backend/employee/
  domain/           plain dataclasses (SourceEmployee, errors); no Django, no HTTP
  application/      use cases: SyncEmployees (fetch → validate → apply), ports (SourcePort, StorePort)
  infrastructure/   orbis_adapter (requests), persistence (ORM store), crypto (Fernet), schedule, tasks (Celery), container
  admin/            Django Admin pages: employees, runs, events, data source, schedule, sync now
  models.py         Django models (ORM)
  public.py         the ONLY import surface for other modules
  tests/
```
- **Flow:** Celery Beat (or the admin "Sync now" button) → task `employee.sync` → `SyncEmployees` → adapter reads all pages of the active data source → validates everything → applies all changes in one DB transaction → records the run and events.
- **Scheduling:** `django-celery-beat` `PeriodicTask`, exposed in a purpose-built admin page (same pattern as `AttendanceSchedule`). The generic beat admin stays superuser-only (already done in 004).
- **Frontend:** none in this feature. A later feature adds a DRF API on top of `employee.public`.
- **Dependencies (AR-11):** `employee` → nothing else in Timely (it only uses Django, Celery, `django_celery_beat`, `requests`, `cryptography`). Other modules → `employee.public` only. No cycles.

## 3. Data Model and Ownership
All tables are owned by `employee` (AR-8). ORBIS stays the source of truth; Timely holds a snapshot (spec OQ-4). Ordinary ORM tables, default integer ids (D-24 is OPEN; this follows the existing `attendance` models).

```
DataSource                         (AC-9.1 to 9.3, 8.4)
  name: char unique — label
  base_url: URL — scheme + host (http/https), no embedded credentials
  employees_path: char — default "/api/v1/directory/employees/"
  auth_header: char — default "Authorization"
  auth_prefix: char — default "Bearer" (blank = send the token alone)
  token_encrypted: text — Fernet ciphertext; never shown, never logged
  timeout_seconds: int — default 30
  is_active: bool — partial unique constraint: at most one True
  created_at / updated_at

Office(orbis_id unique, code, name)
Department(orbis_id unique, name)
Team(orbis_id unique, name, department → Department null)
Designation(orbis_id unique, name)

Employee                           (AC-1.1, 4.x, 6.x, 9.6)
  employee_id: char unique — the source's employee_id
  entra_object_id: char null, email: char, full_name, first_name, last_name: char
  status: char — stored exactly as received ("active", "inactive", …)
  joining_date: date null, last_working_date: date null, work_location: char blank
  office → Office null, department → Department null, team → Team null, designation → Designation null
  supervisor_employee_id: char blank — plain id, no foreign key (the supervisor may be synced later)
  source_updated_at: datetime (UTC, aware) null
  first_seen_at, last_synced_at, changed_at: datetime — Timely-side times
  (direct_reports_count is not stored; derivable from supervisor_employee_id)

SyncRun                            (AC-7.1, 4.5, 8.1)
  trigger: scheduled | manual · requested_by: user null · source_name: char (copy, survives source edits)
  state: queued | running | succeeded | failed · started_at, finished_at
  read_count, new_count, updated_count, inactive_count, reactivated_count, unchanged_count, not_in_source_count
  error_kind: char blank · error_message: char blank (safe text only) · celery_task_id
  constraint: at most one run with state queued/running (AC-3.2)

ChangeEvent                        (AC-4.1 to 4.3)
  run → SyncRun · employee → Employee · kind: new | inactive | reactivated · from_status, to_status · occurred_at

OperationAudit                     (spec §7 auditability, AC-9.3)
  who: user null · action: sync_now | schedule_changed | source_created | source_changed | source_activated | token_changed
  details: json (no secrets) · created_at
```
- **Public interface for other modules:** `employee.public` (§4). Other modules never import `employee.models`, tables or internals (AC-5.3). A cross-module reference stores the plain `employee_id` string (D-31 stays OPEN; no foreign keys across modules).
- **Retention (OQ-9):** `SyncRun` 30 days, `ChangeEvent` 365 days, `OperationAudit` 365 days, by a daily housekeeping task. Employees are never deleted.
- **Migrations:** one initial migration for the `employee` app (plain schema change, no raw SQL).

## 4. API Contract
**No HTTP endpoint in this feature.** The spec puts frontend and any public employee HTTP API out of scope (§9). The admin panel is server-rendered Django Admin (same precedent as feature 004). A later feature adds DRF endpoints over `employee.public`, so no business logic will need to move.

**Internal module interface — `employee/public.py`** (AC-5.1, 5.2; returns frozen dataclasses, never ORM objects or `requests` exceptions):
```
EmployeeDTO: employee_id, email, full_name, first_name, last_name, status, is_active (status == "active"),
             joining_date, last_working_date, work_location, office_code, office_name,
             department_id, department_name, team_id, team_name, designation_id, designation_name,
             supervisor_employee_id, source_updated_at
get_employee(employee_id: str) -> EmployeeDTO | None
list_employees(*, employee_ids: Sequence[str] | None, is_active: bool | None, office_code: str | None,
               department_id: int | None, limit: int = 500, cursor: str | None = None) -> EmployeePage
    EmployeePage: items (tuple of EmployeeDTO), next_cursor (str | None); ordered by employee id internally; max limit 1000;
    at most 1000 ids per call; raises InvalidArgument for bad limit, cursor or list size.
get_sync_status() -> SyncStatusDTO: last_success_at, last_failure_at, last_failure_kind, data_as_of, active_source_name,
                                    employee_count, active_count, inactive_count
```
`is_active` follows PROPOSED rule P-3 in §8a.

## 5. Security
- **Authorisation (server-side, deny by default; spec OQ-11 names PROPOSED):** Django permissions on the `employee` app —
  `view` (employee list, runs, events, status), `sync_now`, `manage_source_and_schedule`. No permission → admin entry hidden and the POST refused with 403 (AC-3.3, 9.4, 6.3). The only actions that change data are POST with CSRF protection.
- **Read-only employees (AC-6.2):** the Employee admin has no add, change or delete permission, for anyone including superusers.
- **Token (D-67, AC-8.4, 9.2):** encrypted with Fernet (`cryptography`, already approved) using the key in env var `EMPLOYEE_TOKEN_ENCRYPTION_KEY` (a new secret; names only in the repo, never the value). The admin form field is write-only (empty on edit; blank keeps the stored token). It is decrypted only inside the adapter call, never stored on objects that are logged, never returned or put in run records/audit details/exception text. Without the key, saving a token and syncing are refused with a clear, secret-free message.
- **Source URL safety (AC-9.2):** only `http`/`https`, no user-info, no fragment. The adapter follows the source's `next` links only when they keep the same scheme and host as the configured base URL (a response can never redirect the token to another host), does not follow HTTP redirects, and stops after 200 pages. TLS certificate verification stays on.
- **Validation:** all invariants live in the application layer (response shape, duplicates, counts); admin forms validate schedule and source input; invalid values are rejected (AC-2.2, 9.2).
- **Errors/logs:** adapter errors are mapped to safe error kinds (`unreachable`, `timeout`, `auth_failed`, `http_error`, `malformed`, `truncated`, `config_error`). Messages contain no URL query, headers, token or response bodies.
- **Audit (AC-3.1, 9.3):** `OperationAudit` records who/when for sync now, schedule changes, source create/edit/activate and token change (a "token changed" flag only, never the value).

## 6. External Systems and Adapters
- **Port:** `SourcePort.fetch_all() -> list[SourceEmployee]`. **Adapter:** `infrastructure/orbis_adapter.py` (read-only GET). ORBIS vocabulary (`department.id`, `office.code`, …) stays inside the adapter and the persistence mapper (AC-8.4, P4).
- **Request:** `GET {base_url}{employees_path}?status=all` with the configured header; follows `next` until `null` (AC-9.5). Timeouts: connect 5 s, read `timeout_seconds`.
- **Failure behaviour (AC-8.1, 8.3):** the adapter reads every page first and the use case validates before any write. A run fails — and changes nothing — when: the source is unreachable or times out, returns 401/403, another HTTP error, malformed JSON or a record without `employee_id`, a **duplicate `employee_id`** (P-4), or fewer records than the reported `count` (truncated). Otherwise all changes are applied in **one transaction** (AC-8.3).
- **Apply rules (AC-4.x):** per employee compare the stored fields with the source; new → create + `new` event; status becomes non-active → `inactive` event; becomes active again → `reactivated` event; other field changes → update and count only; identical → no write, no event. Lookup rows are created or renamed by ORBIS id. Employees missing from the response are untouched and counted `not_in_source` (AC-8.5).
- **Overlap (AC-3.2):** the database constraint allows one queued/running run; a second request is refused (manual) or skipped (scheduled). Runs stuck as queued > 15 min or running > 3 h are marked failed by housekeeping (values from environment with those defaults, as in 004).
- **Background jobs (D-59, D-65):** reuses Celery + Redis + Beat; no new package. Task `employee.sync` and task `employee.housekeeping` (daily).

## 7. Frontend
None in this feature (spec §1, §9). **BFF / Route Handlers:** None.

## 7a. Admin Panel (Django Admin, English)
| Page | Content | Permission |
|---|---|---|
| Employees | read-only list; search by id, email, name; filters: status, office, department, designation, work location | view |
| Sync runs | list with counts and result; header panel with last success, last failure, "data as of", active source and active schedule; **Sync now** button | view; button needs `sync_now` |
| Change events | read-only; filter by kind (new / inactive / reactivated), run, date | view |
| Data source | create/edit sources, write-only token, **Set active**, "Test connection" (reads page 1 only, writes nothing) | manage_source_and_schedule |
| Schedule | mode **Interval** (every N minutes) or **Daily** (time HH:MM, Asia/Dhaka); on/off; shows last run, next run, last result | manage_source_and_schedule |

Schedule rules (AC-2.1, 2.2): interval 5 to 1440 minutes (P-5); daily time 00:00–23:59; saved through `django_celery_beat` (`IntervalSchedule` / `CrontabSchedule`), which Beat's DatabaseScheduler picks up without a restart. A default schedule is created **disabled** (daily 02:00) by `manage.py setup_employee_schedule`.

## 8. Tech Choices & Trade-offs
| Decision | Options considered | Chosen | Status | Why |
|---|---|---|---|---|
| Model | one flat table; relational lookups | Employee + 4 lookup tables, supervisor as plain id | CONFIRMED (owner, 2026-10-15) | Rename in one place; clean filters; no cross-sync ordering problem |
| Module style | plain app; clean architecture | Same layout as `attendance` | PROPOSED | Consistent with D-61, adapter testable with fakes |
| Scheduling | own scheduler; django-celery-beat | `django-celery-beat` via admin page | PROPOSED | Already approved (D-59/D-62); no restart needed |
| Token storage | env only; encrypted in DB | Encrypted in DB (Fernet) | CONFIRMED (D-67) | Admin-managed source |
| Atomicity | per-record apply; whole run | One transaction per run | PROPOSED | AC-8.3; 1500 records fit comfortably |
| Change detection | compare `updated_at`; compare field values | Compare field values | PROPOSED | A renamed department/office may not change an employee's `updated_at` |

**New dependencies / infrastructure:** None (reuses `requests`, `cryptography`, Celery, Redis, django-celery-beat). **One new secret:** `EMPLOYEE_TOKEN_ENCRYPTION_KEY` (generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`, put in `backend/.env`; the agent never reads `.env`).

## 8a. Decisions for the owner (all PROPOSED until approved)
- **P-1 (worker/queue):** route employee tasks to a new queue `employee_sync` and add it to the *existing* sync worker (`-Q attendance_sync,employee_sync`) in the attendance supervisor and its service templates. This touches approved 004 code (a one-line queue list + docs) and needs the owner's approval; a long attendance sync can delay an employee sync slightly. Alternative: a third dedicated worker (more processes to supervise).
- **P-2 (permissions):** names `view`, `sync_now`, `manage_source_and_schedule` (spec OQ-11, still PROPOSED).
- **P-3 (status):** only `status == "active"` counts as active; any other value is stored as received and treated as not active.
- **P-4 (duplicates):** a duplicate `employee_id` in one response fails the whole run.
- **P-5 (interval limits):** 5–1440 minutes.
- **P-6 (menu):** `Employee` appears as its own admin section; the existing attendance step-ordered menu (`TimelyAdminSite`) is only extended to list it, with no change to attendance behaviour.

## 9. Traceability Matrix
| Spec item | Plan section | Notes |
|---|---|---|
| US-1 / AC-1.1 | §3, §6 | paged full fetch, first load |
| US-2 / AC-2.1, 2.2 | §7a, §6 | interval or daily, validated |
| US-3 / AC-3.1–3.3 | §5, §6, §7a | Sync now, overlap constraint, permission |
| US-4 / AC-4.1–4.5 | §3, §6 | events, counts, repeat-safe |
| US-5 / AC-5.1–5.3 | §4, §10 | `employee.public`, boundary test |
| US-6 / AC-6.1–6.3 | §7a, §5 | read-only list |
| US-7 / AC-7.1, 7.2 | §3, §7a | SyncRun + status panel |
| US-8 / AC-8.1, 8.3, 8.5 | §6 | validate then single transaction |
| AC-8.4 / US-9 / AC-9.1–9.6 | §3, §5, §6, §7a | DataSource, token, `status=all`, lookups |

## 10. Testing Strategy
- **Use-case tests (fake source and store):** first load; new/inactive/reactivated; unchanged repeat writes nothing; absent employee untouched; duplicate id, missing id, truncated count, malformed data → no change; counts correct.
- **Adapter tests (mocked HTTP):** paging via `next`, `status=all`, auth header, 401/403, timeout, redirect refused, foreign-host `next` refused, page cap, no token in any exception or log text.
- **Persistence tests (PostgreSQL):** one-active-source constraint, one-active-run constraint, rename of a department updates all employees' view, retention deletes.
- **Crypto tests:** round trip, missing key, token never in `repr`, admin form write-only.
- **Admin tests:** list is read-only for superuser; permission matrix (view / sync_now / manage) for every page and POST; Sync now queues a run and audits; schedule form validation; "Test connection" writes nothing.
- **Schedule tests:** interval and daily create the correct `django_celery_beat` objects; default created disabled.
- **Public interface tests:** DTO shape, filters, cursor paging, argument validation.
- **Boundary test:** `employee` imports no other Timely app; other apps import only `employee.public` (AC-5.3).
- **Manual (recorded separately in validation):** real ORBIS read with the owner's token, run end to end through Celery, schedule change observed by Beat.

## 11. Risks & Mitigations
- Token key lost or changed → stored tokens unreadable → the admin shows "re-enter token"; no data loss.
- A different source with another id space for office/department/team → lookup ids could clash → documented limit: replacement source must be the same shape **and id space** (spec §9).
- Source changes its schema → run fails as `malformed`, no data changed.
- ORBIS marks everyone inactive by mistake → applied as sent (no threshold, owner decision OQ-8); `ChangeEvent` history lets the owner see exactly what changed.
- Employee id reused for a different person in the source → treated as the same employee; accepted by "ORBIS is the source of truth".
- Queue sharing delays (P-1) → short, accepted unless the owner chooses a dedicated worker.

## 12. Constitution Check
| Principle | Compliant? | Notes |
|---|---|---|
| P1 Spec first, approval gates | Yes | Plan follows approved spec + A-1; tasks and implementation wait for approval |
| P2 Decisions labelled | Yes | §8a lists everything PROPOSED; OQ-11 remains PROPOSED |
| P3 Modular monolith | Yes | `employee` module, public interface only, boundary test, no cycles |
| P4 Adapters | Yes | ORBIS only through `orbis_adapter`; vocabulary contained |
| P5 Security/privacy/audit | Yes with owner exception | Token in DB is the D-67 exception; permissions, audit, no secrets in logs |
| P6 Evidence-based validation | Yes | §10; results recorded in `validation.md` |
| P7 Minimal footprint | Yes | No new package or infrastructure; no Docker/WSL; no AI |
| P8 API-first | Yes | No client-facing API yet; logic lives in Django; later DRF API over `employee.public` |

## 13. Change Log
| Date | Change | Reason | Approved by |
|---|---|---|---|
| — | — | — | — |

---
**Status:** Ready for approval · **Approved by:** — · **Date:** —
