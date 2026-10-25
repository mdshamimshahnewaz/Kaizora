# Domain ownership and public interfaces

Identity, system, organizations, clients, resources and projects are installed apps.
The 0005–0008 foundation includes App UI, DRF and command-backed Django Admin;
owner UI/UX acceptance remains pending. Other directories reserve future boundaries.

| Module | Owns | Public operations / planned capabilities |
| --- | --- | --- |
| organizations | Workspace and tenant membership | Scope, provisioning, membership history, owner transfer, trusted assignment summaries; live 0004 policy |
| identity | Login identity, credentials, roles, personal preferences | Sessions, account profile/preferences, current permissions, roles and bounded delegation |
| clients | Client organizations and contacts | Scoped CRUD/archive commands, separate contact capabilities, frozen relationship summaries |
| projects | Delivery projects and operations engagements | Private list/detail, creation, lifecycle, project access grant/end; milestones deferred |
| work_items | Tasks, stories, bugs, dependencies, work history | create/transition work item |
| operations | Request intake, service targets, operational queues | register external request |
| resources | People profiles and teams | Stable no-login profiles, identity-link history and dated team intervals; capacity calendars deferred |
| allocations | Effective-dated project staffing | allocate/release/query period |
| replacements | Coverage, approvals, handover relationships | plan/approve/end coverage |
| timesheets | Actual work, submissions, approvals and corrections | query approved work, submit time |
| commercials | Contracts, rates, billing policies | resolve dated policy/rate |
| billing | Billing runs, source lines, snapshots, adjustments | prepare/approve billing run |
| reporting | Definitions, projections, issued report snapshots | run/publish report |
| customization | Typed field definitions, scoped configuration, values | validate/store/query custom values |
| communications | Templates, delivery requests and outcomes | request approved communication |
| integrations | External IDs, sync adapters and checkpoints | import/register external record |
| audit | Important immutable change events | record authorized domain change |
| system | Operational health endpoints | liveness/readiness |

Billing will ask Timesheets for approved work and Commercials for dated rules.
It must not update time rows. Replacements will reference actual assignments without
changing previous contributors. Reporting may use documented read projections;
reports must not mutate source records or derive history from current roster status.

Each feature spec must define concrete interface signatures, DTOs, errors, actor/scope
checks and transaction ownership before implementing these planned operations.
