# Feature Spec — Employee Sync

> **Purpose:** WHAT is being built and WHY, with no technical solution. Technical decisions are in `plan.md`.
> **Location:** `specs/005-employee-sync/spec.md`. **Rules:** `docs/constitution.md` (P2, P3, P4, P5, P7, P8), `docs/architecture.md`.
> **Process note:** drafted in the conversation on 2026-10-15 and approved by the owner (`spec approved`) as drafted. The Open Questions in §10 were NOT answered by the approval; each must be resolved or explicitly DEFERRED by the owner before the plan is approved.

## 1. Summary
A new `employee` module that copies all employees from another application's API (the "source") into Timely's own PostgreSQL. Scheduled syncs (interval in minutes or once daily, configurable by an administrator) detect new employees and employees who became inactive. An administrator can also run a sync at any time from the admin panel and can see the employee list there. Other Timely modules read employee data only through the module's public interface, never by querying its tables. Frontend pages are a later feature; this feature covers backend and Django Admin only. **[PROPOSED, approved with this spec]**

## 2. User Stories
- **US-1 (P0):** As an administrator, I want all employees loaded from the source API, so that Timely has the full employee list.
- **US-2 (P0):** As an administrator, I want to configure the sync schedule (every X minutes, or daily at a time) without changing code, so that I control how often it runs.
- **US-3 (P0):** As an administrator, I want to run a sync at any time with a "Sync now" action, so that I do not wait for the schedule.
- **US-4 (P0):** As an administrator, I want to see which employees were newly added and which became inactive in each sync, so that I can follow workforce changes.
- **US-5 (P0):** As another Timely module, I want to read employees only through a public interface, so that I never depend on the employee module's tables.
- **US-6 (P1):** As an administrator, I want an employee list in the admin panel with search and filters, so that I can look employees up.
- **US-7 (P1):** As an administrator, I want to see the last success, last failure, run history and "data as of", so that I can trust the data.
- **US-8 (P0):** As the system owner, I want a source outage or bad data to never damage existing employee data, so that a failed sync is harmless.
- **US-9 (A-1, P0):** As an administrator, I want to configure the employee data source (and switch it to another application with the same response shape) from the admin panel, so that no code change is needed.

## 3. Acceptance Criteria
### US-1
- **AC-1.1:** Given an empty Timely employee store, when the first sync runs, then every employee the source returns (all pages) is stored.

### US-2
- **AC-2.1:** An administrator can set the schedule as an interval in minutes or as a daily time, and enable or disable it, from the admin panel; the change takes effect without a code change or restart of the application.
- **AC-2.2:** Invalid schedule values are rejected with a clear message.

### US-3
- **AC-3.1:** Given an authorised administrator, when they click "Sync now", then a sync starts and its result appears in the run history.
- **AC-3.2:** Given a sync is already running, when another is requested (scheduled or manual), then no second run starts.
- **AC-3.3:** Given a user without the dedicated permission, when they try to sync or change the schedule, then access is refused.

### US-4
- **AC-4.1:** A source employee not yet in Timely is created and recorded as a "new" event for that run.
- **AC-4.2:** An employee the source reports as inactive (or no longer returns; see OQ-5) is marked inactive in Timely, never deleted, and recorded as an "inactive" event.
- **AC-4.3:** An inactive employee who becomes active again is marked active and recorded as a "reactivated" event.
- **AC-4.4:** Changed source fields update the stored employee; when nothing changed, nothing is written and no event is recorded (repeat-safe).
- **AC-4.5:** Each run shows its counts: new, updated, inactive, reactivated, unchanged.

### US-5
- **AC-5.1:** Other modules can list and filter employees (by id list, active status, and other agreed fields; paged) and get one employee through the public interface only.
- **AC-5.2:** Returned data is plain read-only objects, never database models.
- **AC-5.3:** A test fails if any other module imports employee internals, or the employee module imports another module.

### US-6
- **AC-6.1:** The admin panel lists employees with search and filters (at least active/inactive).
- **AC-6.2:** Sync-managed fields cannot be edited in the admin panel (see OQ-6).
- **AC-6.3:** Only users with the view permission see the list.

### US-7
- **AC-7.1:** Each run is recorded (trigger: schedule or manual, started, finished, counts, result, error kind).
- **AC-7.2:** Status shows the last successful sync, last failure and the time the data is current as of.

### US-8
- **AC-8.1:** If the source is unreachable, times out, rejects credentials or returns malformed data, no employee is changed and the run is recorded as failed.
- **AC-8.2:** *(Removed by A-1: no mass-deactivation threshold; OQ-8.)*
- **AC-8.3:** A run applies all its changes or none (a partial fetch changes nothing).
- **AC-8.4 (A-1):** The source address is set in the admin panel. The source token is stored encrypted (D-67), is write-only and masked in the admin panel, and never appears in logs, errors, API responses, run records or the repository. The encryption key comes from the environment. The source's own vocabulary stays inside the adapter (P4, P5).
- **AC-8.5 (A-1):** Employees absent from the source response are left unchanged; the run records how many were "not in source".

### US-9 (A-1)
- **AC-9.1:** An authorised administrator can create and edit the data source (name, base URL, endpoint, token) and mark one source active; only one is active at a time.
- **AC-9.2:** Invalid URLs are rejected with a clear message; the token is never displayed after saving.
- **AC-9.3:** Changing the source, its token or its active flag is audited (who, when; never the token value).
- **AC-9.4:** A user without the manage permission is refused.
- **AC-9.5:** The employee list request asks the source for all statuses (active and inactive) and follows the source's paging until all pages are read.
- **AC-9.6:** The data model keeps ORBIS ids for office, department, team and designation, stored in lookup tables, and the employee's supervisor as a plain employee id (no link).

## 4. Operations Clients Need
| Operation | Who may perform it | Related AC |
|---|---|---|
| Sync now | Administrator with the dedicated sync permission (**OPEN**: exact permission names) | AC-3.1, 3.3 |
| View and change the schedule | Administrator with the dedicated schedule permission (**OPEN**) | AC-2.1, 2.2 |
| List employees in the admin panel | Administrator with the view permission | AC-6.1 |
| View run history, change events and status | Administrator with the view permission | AC-4.5, 7.1, 7.2 |
| Read employees from another module | Timely modules, through the public interface | AC-5.1 |

## 5. Data and Ownership (business level)
- The `employee` module alone owns the employee records, sync runs and change events. The source application stays the source of truth; Timely does not write back.
- Sensitivity: personal data of employees; admin access is permission-gated, and sync-now and schedule changes are audited (P5).
- Retention/freshness: freshness follows the schedule; retention of runs and events is OPEN (OQ-9).

## 6. External Systems and Dependencies
- **Source application API** (read-only): returns all employees. Which application, its URL, authentication and fields are OPEN (OQ-1 to OQ-4). Reached only through a backend adapter (P4).
- Depends on the existing background-job setup approved for attendance (D-59), if the plan reuses it. Whether new packages are needed is OQ-10; none are assumed.
- Does not depend on the attendance module. Linking employees to attendance punches (EID) is out of scope.

## 7. Non-Functional Requirements
- Performance: OPEN (employee count and time limits, OQ-3).
- Security: server-side authorisation, dedicated permissions, no secrets in logs (P5).
- Auditability: record who ran "Sync now" and who changed the schedule. The wider audit event list stays under D-30.
- Accessibility/i18n: Django Admin in English, as in feature 004.

## 8. Edge Cases & Error States
- Source down, slow, returns an authentication error or malformed or truncated data.
- Empty response, or a sudden large drop in employees.
- Duplicate employee id inside one response; a record missing its id.
- An employee's id changing in the source (OPEN, treated as a new employee until decided).
- Manual sync requested while a scheduled run is in progress.
- Invalid schedule values; schedule disabled.
- Employee removed and later returned.

## 9. Out of Scope
- Frontend pages and any public HTTP API for employees (later feature).
- Creating, editing or deleting employees in Timely (see OQ-6); write-back to the source.
- Linking employees to attendance punches or to login accounts and roles.
- Photos, documents and payroll data.
- Field mapping configuration: a replacement source must return the same response shape as ORBIS (A-1).
- Historical employee snapshots beyond the change events.

## 10. Open Questions
Resolved by Amendment A-1 (owner, 2026-10-15), except OQ-11.
- **OQ-1 (RESOLVED):** Source is ORBIS, configured as an admin-managed Data Source (name, base URL, endpoint, token); one active at a time; the same response shape is assumed (`count`, `next`, `previous`, `results[]` with `employee_id`, `entra_object_id`, `email`, `full_name`, `first_name`, `last_name`, `status`, `joining_date`, `last_working_date`, `department`, `team`, `designation`, `office`, `work_location`, `supervisor`, `direct_reports_count`, `updated_at`).
- **OQ-2 (RESOLVED):** Token stored encrypted in the database, write-only and masked in admin; key in the environment. Recorded as D-67.
- **OQ-3 (RESOLVED):** Paged (follow `next`), request all statuses; 1500+ employees.
- **OQ-4 (RESOLVED):** `employee_id` is the unique id. Model: an `Employee` table plus lookup tables for office, department, team, designation (ORBIS ids kept); supervisor stored as a plain employee id; `direct_reports_count` not stored; also `source_updated_at`, `first_seen_at`, `last_synced_at`. ORBIS stays the source of truth; Timely holds a snapshot.
- **OQ-5 (RESOLVED):** Inactive is taken from the source `status` field only; absence from the list changes nothing (AC-8.5).
- **OQ-6 (RESOLVED):** Admin is read-only for employees.
- **OQ-7 (RESOLVED):** Both interval (X minutes) and daily time, selectable in admin; admin shows the active schedule, last and next run and result. Default: daily 02:00, disabled until configured.
- **OQ-8 (RESOLVED, removed):** No mass-deactivation threshold.
- **OQ-9 (RESOLVED):** Run history 30 days, change events 365 days.
- **OQ-10 (RESOLVED):** No new packages (reuse `requests`, `cryptography` and the existing Celery setup).
- **OQ-11 (PROPOSED, not answered):** Permissions `view`, `sync_now`, `manage_source_and_schedule`. The owner must confirm before the plan is approved.

## 11. Change Log
Changes after approval require re-approval (see `docs/sdd-workflow.md` §5).

| Date | Change | Reason | Approved by |
|---|---|---|---|
| 2026-10-15 | **Amendment A-1:** added US-9, AC-8.4/8.5, AC-9.x; removed AC-8.2; resolved OQ-1 to OQ-10; recorded D-67 (encrypted token in the database) | Owner answers on source configuration, model, schedule and token storage | Project owner, 2026-10-15 (`approve amendment A-1`) |

---
**Status:** Approved (US-1 to US-8 and Amendment A-1; OQ-11 still PROPOSED) · **Approved by:** Project owner (`spec approved`; `approve amendment A-1`) · **Date:** 2026-10-15 · **Linked constitution:** `docs/constitution.md` (v1.1)
