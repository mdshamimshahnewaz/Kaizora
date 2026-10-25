# Organizations

Implemented in feature 0003: operator provisioning, scoped queries, membership lifecycle,
append-only change records and owner transfer. Public entry point: `interfaces.py`.
Never import internal models from another domain. Public DTOs are immutable.

Ordinary membership read/manage calls require the future 0004 policy via
`ORGANIZATIONS_PERMISSION_POLICY`; absent policy denies access even to owners.
No permissive policy is installed by this feature. All mutation commands lock the
organization before revalidating access. Django Admin is read-only for these models.

Operator permission: `organizations.bootstrap_organization` (active superusers also
qualify). Provisioning never grants tenant access unless the actor is the chosen owner.
Use `manage.py provision_organization --help`; no default tenant/backfill is created.
