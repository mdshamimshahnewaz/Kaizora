ORGANIZATION_KEYS = frozenset(
    {
        "memberships.read",
        "memberships.manage",
        "roles.read",
        "roles.manage",
        "roles.assign",
        "clients.read",
        "clients.manage",
        "contacts.read",
        "contacts.manage",
        "resources.read",
        "resources.manage",
        "resources.link_identity",
        "resources.contact_read",
        "teams.read",
        "teams.manage",
        "projects.create",
        "projects.read_all",
    }
)
PROJECT_KEYS = frozenset(
    {
        "projects.read",
        "projects.manage",
        "projects.transition",
        "projects.reopen",
        "projects.restore",
        "projects.access.read",
        "projects.access.manage",
    }
)
ALL_KEYS = ORGANIZATION_KEYS | PROJECT_KEYS
PRESETS = (
    {
        "name": "Organization administrator",
        "scope_kind": "organization",
        "permissions": sorted(ALL_KEYS),
    },
    {"name": "Member", "scope_kind": "organization", "permissions": []},
    {"name": "Project manager", "scope_kind": "project", "permissions": sorted(PROJECT_KEYS)},
)
