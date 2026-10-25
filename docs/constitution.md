# Kaizora engineering constitution

Version: 1.2 · Updated: 2026-10-18.
Scope: project delivery and client operations in an API-first modular monolith.
SDD means Specification-Driven Development.
This revision expands the existing principles under the owner's documentation setup
request. It does not approve unimplemented product choices or claim production readiness.

## P1 — Specification and authority
Before implementation, document the problem, users, scope, acceptance scenarios,
contracts, migration impact and verification plan. Trace acceptance IDs through tasks
and evidence. Follow [the workflow](sdd-workflow.md); existing user authorisation
remains valid. Never fabricate an approval or silently expand scope.

## P2 — Explicit decisions
Record architectural rationale in ADRs and unresolved choices in
[the decision register](decisions.md). Distinguish implemented facts, confirmed
requirements, proposals, open questions and deferred work. Resolve blockers before
implementing dependent behaviour. Do not invent roles, tenancy or financial policy.

## P3 — Modular ownership
One Django deployment and PostgreSQL database are the default. Modules own their
writes. Cross-module imports use the owner's `interfaces.py`, returning immutable
DTOs rather than models or QuerySets. Declare dependency direction and transaction
ownership. Internal calls run in-process. Service extraction needs evidence and a
separate design covering storage, contracts, retries, identity and consistency.

## P4 — API-first clients and integrations
Web and future mobile clients use versioned DRF APIs. React/Vite is presentation;
Django owns business and authorisation rules. Django Admin must use the same domain
use cases for approvals, billing and corrections. External systems are accessed
through backend adapters with explicit failure and retry behaviour.

## P5 — Security and privacy
Deny access by default. Every future business use case receives actor and organisation
scope and checks access, including Admin actions. Enforce object and field access
server-side. Keep secrets out of frontend bundles, source and logs. Protect session
mutations with CSRF; require HTTPS and secure cookies in production. Never persist
session credentials in browser storage. Audit requirements and retention need explicit
feature decisions. Organization scope is implemented by 0003; configurable role authorization remains 0004.

## P6 — Historical truth and finance
Actual worker, accountable owner, client attribution and billing eligibility are
separate concepts. Allocation and rate changes are effective-dated. Releasing a
member ends an allocation period; it never erases past work. Work-date rules determine
historical classification. Approved corrections preserve prior values and reasons.
Issued financial records require traceable adjustments rather than silent rewrites.

## P7 — Controlled customization
Custom fields extend typed, scoped data. They cannot bypass permissions, approvals
or financial rules. Each feature specifies field validation, lifecycle/versioning,
filtering, reporting and indexing requirements. Historical interpretation must survive
field option changes or retirement. The storage design remains OPEN.

## P8 — Evidence and operability
Test observable behaviour, permission denial and applicable historical regressions.
Enforce module boundaries, regenerate API contracts, and record exact outcomes.
Separate planned checks from executed evidence. Document performance workloads,
limits, rollback and migration consequences where applicable. Never mark an unrun
check as passed or infer production readiness from a development build.

## P9 — Maintainable frontend and dependencies
Use the shared shadcn/Tailwind design system, semantic tokens and Lucide icons.
Preserve accessible and responsive interaction. Reuse the typed API client.
Dependency changes need a documented purpose, compatibility and licensing check;
add infrastructure only when the feature requires it. No unrequested stack migration.

## P10 — User documentation is part of delivery
Every user-facing feature ships with an updated end-user guide covering setup,
permissions, examples, App UI and applicable Admin operations, expected outcomes,
history and troubleshooting. Verification links the guide and records checks against
implemented behaviour. Missing guidance prevents a completion claim; internal-only
changes record why no guide change is applicable. Never publish secrets in examples.

## Amendment process
Record what changed, why and the user direction authorising a material change.
Update affected conventions, ADRs, feature contracts and verification plans. A new
product or security decision outside authorised scope needs owner input; editorial
clarifications and already-requested changes do not require duplicate approval.

| Date | Version | Change | Authority |
| --- | --- | --- | --- |
| 2026-10-18 | 1.1 | Expand existing foundation into a project-wide SDD documentation system | Owner requested adapting Timely documentation to Kaizora |
| 2026-10-18 | 1.2 | Require user-guide delivery with every user-facing feature (P10) | Explicit owner instruction to maintain configuration/example guides with feature completion |

Implemented scope includes foundation, UI foundations, web login/shell/logout and
0003 organization scope, provisioning and membership lifecycle, 0004 roles, and
0005–0008 account, clients, people/teams and projects foundation.
The historical and customization principles constrain future implementation.
