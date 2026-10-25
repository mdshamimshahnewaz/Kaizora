# Timely V4 — Decision Log

> Records project decisions and their status: CONFIRMED, PROPOSED, OPEN, DEFERRED. Only the project owner can promote a decision to CONFIRMED. Agents flag contradictions rather than choosing a side (Constitution P2).
> **This is the single register of OPEN and DEFERRED items.** The OPEN markers in the Constitution (module list, versions, coverage and performance targets, audit events) are tracked here as D-22, D-29 and D-30 rather than repeated elsewhere.

## CONFIRMED
| ID | Decision | Date | Source |
|---|---|---|---|
| D-1 | Constitution amended to v1.1: added P8 (API-first architecture). Wording ratified by the owner after the SDD audit. | 2026-10-09 | Owner approval (option B, then ratification after audit) |
| D-2 | Feature folders are `specs/NNN-slug/` (e.g. `specs/001-example/`), each with `spec.md`, `plan.md`, `tasks.md`, `validation.md`. | 2026-10-09 | Owner approval |
| D-3 | Shared project rules live in `docs/`; reusable templates in `sdd-templates/`. | 2026-10-09 | Owner requirement |
| D-4 | New SDD documents and templates are written in English. | 2026-10-09 | Owner approval |
| D-5 | The legacy files are non-authoritative; `docs/` and the Constitution take precedence. Superseded in practice by D-9. | 2026-10-09 | Owner approval |
| D-6 | Implementation starts only after the owner approves `tasks.md` **and** gives a separate explicit instruction to implement, once per feature. Any change to an approved spec/plan/tasks requires re-approval before implementation continues. | 2026-10-09 | Owner approval of audit D3 |
| D-7 | Status vocabulary: `Draft → Ready for approval → Approved`, with "Approved by / date" in each document. "Reviewed" is dropped. | 2026-10-09 | Owner approval of audit D4 |
| D-8 | A root `AGENTS.md` and `docs/tech-stack.md` will be created. The Constitution's installed-version list stays until amended. | 2026-10-09 | Owner approval of audit D5, D6 |
| D-9 | Legacy `specs/blueprint.md`, root `plan.md`, `SDD-README.md` and `sdd-templates/Example/` are moved (not deleted) to `docs/archive/` as `blueprint.md`, `setup-review.md`, `SDD-README.md` and `Example/`. Done 2026-10-09 at the owner's instruction, with a plain move before the first commit (they were untracked, so `git mv` was not possible). They remain non-authoritative. | 2026-10-09 | Owner approval of audit D7; move ordered by owner |
| D-14 | The Constitution's amendment process: explicit owner approval, with reason, version and date in the amendment log. | 2026-10-09 | Owner approval of audit D2 |
| D-15 | `specs/README.md` columns: link, current stage, approved through (Spec/Plan/Tasks), implementation authorised (Y/N), validation. Approver and date live only in each document's footer. | 2026-10-09 | Owner approval of audit D8 |
| D-16 | Feature folders: 3-digit sequential number, kebab-case slug, never renamed or reused. | 2026-10-09 | Owner approval of audit D9 |
| D-17 | Git hygiene: root `.gitignore` is created before anything is staged. The owner directs the docs commit. Agents never commit unless asked. | 2026-10-09 | Owner approval of audit D10 |
| D-18 | Installed but unapproved dependencies (allauth, simplejwt, django-filter, etc.) are recorded only, not removed. Keep/remove is decided in the auth spec. | 2026-10-09 | Owner approval of audit D11 |
| D-19 | Approved documents carry a dated change log. Changes require re-approval of affected downstream documents. | 2026-10-09 | Owner approval of audit D12 |
| D-50 | The SDD setup is final (audit Phase 6 signed off). | 2026-10-09 | Owner sign-off |
| D-51 | Document flow: the spec is drafted in the conversation and written to a file only after approval. Plan, tasks and validation are written as files marked `Ready for approval`. | 2026-10-09 | Owner approval |
| D-52 | Reusable feature prompt is `sdd-templates/feature-prompt.md` (five input fields). Stage transitions use the fixed phrases in `sdd-templates/stage-prompts.md`. | 2026-10-09 | Owner approval |
| D-53 | The rules in `docs/architecture.md`, `docs/api-conventions.md` and `docs/frontend-api-client.md` stay PROPOSED (D-10); features may rely on them and must flag deviations. | 2026-10-09 | Owner decision |
| D-55 | Authentication (resolves D-21): Microsoft Entra ID single-tenant sign-in run by a Django adapter; Django database sessions carried by the Next.js BFF in an HttpOnly cookie; roles are Django groups assigned in Timely (token claims ignored); users created on first sign-in with no roles; sessions 30 min idle and 8 h absolute; Timely-only logout. Details: `specs/002-authentication`. | 2026-10-11 | Owner approval of spec 002 (OQ-1 to OQ-8 accepted) |
| D-56 | Browser-to-Django path (resolves D-20 for authentication): the browser talks only to Next.js; three BFF Route Handlers are registered in `docs/architecture.md` §3. | 2026-10-11 | Owner approval of spec and plan 002 |
| D-57 | Installed auth packages (D-18 outcome): `requests`, `PyJWT`, `cryptography` approved for the Entra adapter; `django-allauth`, `djangorestframework_simplejwt` and `oauthlib` removed from `requirements.txt`. | 2026-10-11 | Owner approval of spec 002 OQ-7 |
| D-58 | Foundation fixes in spec 002 (part of D-27): `SECRET_KEY`, `DEBUG` and `ALLOWED_HOSTS` come from the environment; `system-info` is superuser-only. | 2026-10-11 | Owner approval of spec 002 OQ-6 |
| D-59 | Background jobs for attendance sync (resolves D-40 for spec 004 only): Celery + django-celery-beat with a Redis broker. Packages `celery`, `django-celery-beat`, `redis` and the MSSQL driver `mssql-python` are approved for `specs/004-attendance-sync`. Redis is a native install (no Docker/WSL); on Windows workers use `--pool=solo`, one worker per queue. Production hosting of Redis, workers and beat stays OPEN. | 2026-10-14 | Owner approval of spec and plan 004 |
| D-60 | Attendance date/time are stored as local Asia/Dhaka values exactly as UNIS provides them, without UTC conversion. This is an owner-approved exception to the UTC rule in `docs/api-conventions.md` §2, limited to attendance punches. | 2026-10-14 | Owner approval of spec 004 (AC-D.2) |
| D-61 | First module structure (partial answer to D-22): the `attendance` app is a clean-architecture module (`domain/`, `application/`, `infrastructure/`, `public.py`). Other code may import only `attendance.public`; this is enforced by an automated import test. Punches live in a raw-SQL, monthly-partitioned PostgreSQL table owned only by `attendance`. | 2026-10-14 | Owner approval of plan 004 |
| D-62 | `django-celery-beat` 2.9.0 declares `Django<6.1` but was verified to work on Django 6.1.2 (check, migrations, saving a periodic task). It is installed with `--no-deps` from `backend/requirements-beat.txt` and re-verified on every Django or beat upgrade. | 2026-10-14 | Owner decision at task T1 |
| D-64 | Attendance operations are managed in Django Admin (spec 004 Amendment A-1, approved 2026-10-15): schedule, sync now, retry, backfill jobs, reconciliation views, operations health and an audit log, with six dedicated permissions. Accepted defaults: backfill span limit 366 days and extra confirmation plus the large-backfill permission above 31 days; the generic django-celery-beat admin is superuser-only; retention 30 / 2 / 365 days (task events / heartbeat / audit); task results kept in the module's own `TaskEvent` table instead of `django-celery-results`; new folders `scripts/windows/` and `deploy/`. | 2026-10-15 | Owner approval of spec, plan §13a and tasks T24–T42 |
| D-65 | Reliable startup for attendance (A-1): the repository's own supervisor (`manage.py run_attendance_services`) starts the two workers and Beat; Windows development uses a per-user at-sign-in scheduled task (no administrator rights, runs while signed in); production reference is Linux systemd units (templates only, hosting stays OPEN); a Windows service wrapper (NSSM / WinSW) would be a new tool and needs separate approval. | 2026-10-15 | Owner approval of Amendment A-1 (OQ-A4, OQ-A5, OQ-A6) |
| D-66 | Raw punch data menu (A-4, approved): view and audited edit of date, time, rfid and geolocation; office, eid and terminal read-only; no add or delete; a moved punch is not re-inserted by sync (original key kept in `PunchEditLog`, which is never purged); permissions `view_punches` and `edit_punches`; edits recorded with old and new value in `PunchEditLog`; UNIS stays the source of truth. Lifts the earlier 'no local edit' rule in this scope only. | 2026-10-15 | Owner approval of Amendment A-4 (spec, plan, tasks), 2026-10-15 |
| D-67 | Employee sync (spec 005, Amendment A-1): the source application is configured from the admin panel; its access token may be stored in the database encrypted (key from the environment), write-only and masked in admin, and never logged or returned. This is an owner-approved exception for data-source tokens only; Constitution text is unchanged. | 2026-10-15 | Owner approval of Amendment A-1 |
| D-63 | UNIS connections use `UNIS_TRUST_SERVER_CERTIFICATE=True` for all offices: the UNIS servers present certificates this machine does not trust, so server-certificate validation is skipped (traffic stays encrypted, the server is not authenticated). Accepted by the owner for the internal network. Revisit if UNIS certificates become trusted or the sync runs across an untrusted network. | 2026-10-14 | Owner decision (set in `backend/.env`) |

Implementation status of the audit decisions: D-6, D-7, D-8, D-9, D-15, D-16, D-17 (root `.gitignore`) and D-19 (change-log sections in templates) are applied. D-14 and D-18 are in effect. The docs commit under D-17 is directed by the owner and has not been made.

## PROPOSED (awaiting owner review)
| ID | Decision | Where |
|---|---|---|
| D-10 | The rules in `docs/architecture.md`, `docs/api-conventions.md`, `docs/frontend-api-client.md` (except items marked CONFIRMED there). | those documents |
| D-11 | Error envelope with `type`, `title`, `status`, `code`, `detail`, `errors[]`, `request_id`. | api-conventions §4 |
| D-12 | URL scheme `/api/v1/<module>/<resource>/`. | api-conventions §1 |
| D-13 | Paginated lists only; `{count,next,previous,results}` envelope. | api-conventions §3 |
| D-54 | Modular-monolith rules AR-11 to AR-14: declared one-directional dependencies without cycles, in-process module communication (internal HTTP needs an approved requirement), single-owner transaction boundaries, and client API parity for web and mobile. Feature plans also record module ownership, dependencies, public interfaces, data access and transaction boundaries. Extraction into separately deployed services stays subject to a separate approved decision (D-41). | architecture sections 2 and 5 |

## OPEN
| ID | Decision | Options / recommendation |
|---|---|---|
| D-20 | Browser-to-Django path | Resolved for authentication by D-56. Other features: everything through the Next.js server (recommended) vs browser calls Django directly. |
| D-21 | Authentication mechanism | **Resolved by D-55.** |
| D-22 | Backend module list, folder structure, boundary enforcement | Proposed in the first feature plan that needs it. Partly answered by D-61 (`attendance` module and its boundary test); the overall module list stays OPEN. |
| D-23 | Error format | RFC 9457 problem+json (recommended) vs custom envelope. |
| D-24 | ID type, page sizes, time-zone handling | UUID vs integer; defaults and maximums. |
| D-25 | Contract tooling | drf-spectacular + openapi-typescript (new dependencies) vs manual contracts in plans. |
| D-26 | Frontend runtime validation / lint enforcement tooling | New dependencies; needs approval (P7). |
| D-27 | Foundation issues: hardcoded `SECRET_KEY`, `DEBUG = True`, unauthenticated `system-info` | Resolved by D-58 (implemented in spec 002; validation pending). |
| D-28 | Which parts of the legacy blueprint, if any, to migrate into `docs/` before archival (archival itself is decided in D-9). | Migrate only approved content, case by case. |
| D-29 | Approved supported versions, test coverage target, performance targets, data retention | Constitution §3/§4. |
| D-30 | Audit events, audit retention, access-revocation targets | Constitution P5. |
| D-31 | Cross-module foreign keys and joins; distributed transactions and the outbox pattern | Undecided. Each feature plan states how it references another module's data (architecture §4, AR-13). |

## DEFERRED
| ID | Decision |
|---|---|
| D-40 | Background jobs, real-time (SSE/Channels), idempotency keys, rate limiting, CORS/CSRF settings. Background jobs are decided for attendance sync only (D-59); other uses stay deferred. |
| D-41 | Docker/microservice split (out of scope per Constitution). |
