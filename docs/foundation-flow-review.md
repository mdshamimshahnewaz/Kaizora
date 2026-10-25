# Foundation flow review

This guide covers the owner-requested 0005–0008 implementation. Execution evidence
and remaining verification limits live in [the delivery record](specs/0005-0008-delivery.md).
UI/UX acceptance belongs to the owner after trying the complete flow.

## Concepts shown in the UI

| Name | Meaning | Does not automatically grant |
| --- | --- | --- |
| Account | A person's login and personal preferences | Organization or project access |
| Organization member | A login allowed into that organization | Every business permission |
| Client | A customer referenced by projects | A login account |
| Person / resource | Stable identity for someone who does work, including contractors without login | Login, project access or billability |
| Team | Dated grouping of people | Project access or a role |
| Project access | A member's project-scoped role | Staffing allocation, time approval or billing eligibility |

## Suggested review journey

1. Sign in and open **My account**. Change your own name, theme and timezone.
   Check save feedback and persistence after reload. Identity fields stay read-only.
2. Open **Organizations** and choose your organization. Its settings manage
   organization members and roles. Existing login accounts can be created through
   Django Admin; adding a person resource is a separate operation.
3. Prepare the roles needed by your team. The Project manager preset is a
   project-scoped role definition; it is assigned to a project, not as an
   organization role. Creating a role does not silently assign it to anyone.
4. Open **Clients**, add a client, open its details, and add business contacts.
   Check that the client code is clear before saving because it is immutable.
5. Existing members can be selected directly in Teams or Project Workforce.
   Open **People → Create person** only for no-login workers; code is optional.
   **Add existing member** is available if you want to prepare a resource first.
6. Open **Teams**, create a team and select an existing member or resource using
   the searchable dropdown, with a start date. End dates
   are exclusive: ending on a date means the person is no longer in that team
   on that date. The first version supports prospective changes only.
7. Open **Projects**, create a delivery project or operations engagement, choose
   a client when applicable, and choose its initial manager and project role.
   An internal project can have no client. The initial access grant belongs to
   the same atomic operation as project creation.
8. Open the project details, edit its basic information, inspect access and try
   the allowed lifecycle actions. Projects begin as drafts; reopening and
   restoring are explicit privileged actions.
9. Project **Workforce → Add worker** records members/no-login resources without
   granting app access. Task/time logging is not yet implemented.
10. Repeat appropriate create/edit/lifecycle actions through Django Admin with
   an authorized staff account. Staff status alone does not bypass organization
   or project permissions.

## Acceptance questions

- Can you find the next action without knowing API paths or database IDs?
- Are organization, client, person, team and project concepts distinguishable?
- Do create/edit forms ask for the right amount of information?
- Are denied actions, empty lists, save failures and stale edits understandable?
- Is it clear which changes preserve history, and which dates affect membership?
- Does the navigation remain usable with a collapsed sidebar and narrow screen?
- Can an ordinary member see only the records and actions assigned to them?

Record confusing steps and desired changes against the feature number. This is
foundation scope: tasks/Gantt, staffing/replacements, time tracking, billing,
custom fields and operational queues are subsequent features.
