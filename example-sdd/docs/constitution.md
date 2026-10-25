# Project Constitution — Timely V4

> **Purpose:** This document records the non-negotiable principles of Timely V4. Every spec, plan, task and change must be consistent with it.
>
> **Status labels:** CONFIRMED (explicitly approved by the project owner), PROPOSED (suggested, not yet approved), OPEN (undecided), DEFERRED (postponed). Only the project owner can promote a decision to CONFIRMED.

## 1. Mission
Timely V4 is an internal employee attendance and workforce-information application. It is built with Django REST Framework, Next.js and PostgreSQL, and is developed incrementally from approved specifications. **[CONFIRMED]**

Features of the old Laravel application are not automatically in scope for V4. A feature enters scope only when explicitly approved. **[CONFIRMED]**

## 2. Core Principles

**P1. Spec first, with approval gates.** **[CONFIRMED]**
- Work follows Constitution → Spec → Plan → Tasks → Implement and Validate.
- No stage starts until the project owner explicitly approves the previous one and asks to proceed.
- This applies to all new work and all future changes.
- Existing foundation code does not need to be removed because it predates this Constitution. Any future change to it follows the approved workflow.
- Test: every change traces to an approved task, and every task to an approved spec item.

**P2. Decisions are labelled and never silently resolved.** **[CONFIRMED]**
- Each decision is marked CONFIRMED, PROPOSED, OPEN or DEFERRED.
- A proposal becomes CONFIRMED only through the project owner's explicit approval.
- Agents flag contradictions rather than choosing a side.
- Specs do not invent requirements, tenant details, permissions or owners.

**P3. Modular monolith with pragmatic Clean Architecture.** **[CONFIRMED: direction]**
- One deployable Django application, organised into modules with explicit responsibilities and controlled dependencies.
- Domain, application, infrastructure and presentation are separated only where complexity justifies it.
- No empty layers, speculative abstractions or microservice split without an approved requirement.
- A module does not reach into another module's internals or data.
- **OPEN:** module boundaries, the module list, folder structure, and how boundaries are enforced.

**P4. External systems sit behind adapters.** **[CONFIRMED: direction]**
- ORBIS, UNIS, Microsoft Entra and Graph, and any AI provider are accessed only through adapters.
- Vendor schemas and formats do not leak into domain logic.
- UNIS access is read-only.
- **OPEN:** source-of-truth decisions, connection methods and integration details for each system, until approved.

**P5. Security, privacy and auditability.** **[CONFIRMED]**
- Server-side authorisation and least-privilege access are required design principles.
- Access is never granted by trusting client input or token claims alone.
- Secrets never appear in source, logs, API responses, diagnostics or documents.
- Configuration comes from the environment.
- Tokens are not stored in browser storage.
- Diagnostic endpoints are not publicly exposed in production.
- Security-relevant events are auditable.
- **OPEN:** the specific audit events, audit retention periods and access-revocation targets.

**P6. Evidence-based validation.** **[CONFIRMED]**
- Each acceptance criterion has an automated test where feasible.
- A requirement is marked Passed only when the relevant test or validation was actually executed and its result recorded.
- Planned validation and executed validation are reported separately.
- Failures are investigated, not worked around.

**P7. Minimal footprint and protected working code.** **[CONFIRMED]**
- No Docker or WSL.
- No unapproved dependencies or infrastructure.
- No unauthorised changes to existing functionality.
- No AI or ML implementation without explicit approval and its own approved scope and specification. This includes model downloads, model training and ML frameworks.
- AI must not make consequential employee decisions autonomously.
- AI data access follows the same authorisation rules as all other application functionality.

**P8. API-first architecture.** **[CONFIRMED]** *(added in v1.1)*
- Django REST Framework is the authoritative application API and business-logic layer. Next.js is the presentation layer.
- Frontend business operations and data access go through the approved Django API. There is no direct frontend-to-PostgreSQL access.
- Next.js Route Handlers/BFF are allowed only for explicitly justified frontend-specific needs. They never replace Django business APIs.
- External systems are reached only through backend adapters (P4). Internal Django modules may communicate through defined internal interfaces; not every operation needs an HTTP endpoint.
- Every feature specification and plan addresses its API contracts, data ownership, security and testing.
- Detailed rules live in `docs/architecture.md` and `docs/api-conventions.md`, and they must stay consistent with this principle.
- Test: every feature's plan states its API contract, data owner, security design and test strategy, and no frontend code accesses PostgreSQL or an external system directly.

## 3. Technology Constraints
- **Foundation, preserved:** Django and DRF backend, Next.js frontend, and PostgreSQL. **[CONFIRMED]**
- **Currently installed (verified read-only on 2026-10-09):** Python 3.14.5, Django 6.1.2, DRF 3.18.3, Psycopg 3.3.6, django-environ 0.14.0, Node 24.18.0, Next.js 16.4.0, React 19.3.0, TypeScript 5.9.3, PostgreSQL server 18.4. These are facts about the current environment, not approved version requirements.
- **Approved supported versions:** **[OPEN]**
- **Development environment:** Windows, local PostgreSQL. **[CONFIRMED]**
- **Production hosting, deployment, networking, secrets management, backups:** **[OPEN]**
- **Background jobs and real-time:** Procrastinate, SSE, Channels and Celery are proposals only. **[OPEN]**
- **Application architecture:** API-first per P8. Next.js presentation layer; DRF authoritative API and business logic. **[CONFIRMED]**
- **Must avoid:** Docker, WSL, and unapproved dependencies or infrastructure. **[CONFIRMED]**

## 4. Quality Bar
- Test coverage target: **[OPEN]**
- Performance targets: **[OPEN]**
- Data retention and freshness requirements: **[OPEN]**
- Security baseline: P5 **[CONFIRMED]**
- Validation standard: P6 **[CONFIRMED]**

## 5. Out of Scope (project-wide)
- Docker and WSL **[CONFIRMED]**
- AI and ML features until separately approved **[CONFIRMED]**
- Old Laravel or other ORBIS features not explicitly chosen for V4 **[CONFIRMED]**
- Microservice deployment **[PROPOSED]**

## 6. Amendment Process
Amendments require the project owner's explicit approval. Each records its reason, version and date in the amendment log below. **[CONFIRMED]**

---
**Version:** 1.1 · **Last updated:** 2026-10-09 · **Status:** Approved by the project owner

**Amendment log**
- v1.1 (2026-10-09): Added P8 (API-first architecture) and the matching Technology Constraints line. Reason: the project owner required an API-first architecture across all application features. The amendment was first applied on the owner's choice of "amend to v1.1" before the owner had reviewed the final wording.
- v1.1 ratification (2026-10-09): after the SDD audit flagged this, the project owner reviewed the P8 wording and approved it as written. P8 and the Technology Constraints line are CONFIRMED from this date. The Amendment Process (§6) was also confirmed (status label only; its wording is unchanged apart from pointing to this log). No other content changed.
