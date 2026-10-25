# 0009 — Simple resource selection

Owner authorized implementation on 2026-10-18: select existing users directly with searchable dropdowns; support no-login workers managed by a TL/PM. UI/Admin and user-guide delivery required. Acceptance remains pending.

- AC1: Team assignment accepts an active organization member directly, creates/reuses its stable resource identity atomically, and does not create a login or duplicate a live identity.
- AC2: No-login resources remain supported. Project workforce roster can contain either kind; adding a worker never grants system/project access. Only a project manager may change the roster, readers may see its minimal labels.
- AC3: Searchable, paginated member/resource pickers stay tenant scoped, discard stale results and support keyboard use. Member search matches username/name.
- AC4: Existing resource identities, team intervals and project grants remain intact. Roster ending preserves records and rejects stale versions. Inactive/foreign members, retired resources and archived projects reject new assignment. Invalid assignments roll back automatic identity creation.
- AC5: App and Django Admin use the same commands. Document setup/examples and distinction between workforce membership and login access.

Scope is workforce identity/roster foundation. Task/time entry, proxy timesheets, allocation capacity, rates and billing remain separate future features; the roster is their future reference, not a claim that tracking work is implemented.
