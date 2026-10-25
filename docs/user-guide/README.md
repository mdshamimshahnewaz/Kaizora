# End-user guide

Canonical editable source: [HTML guide](../../frontend/public/user-guide/index.html).
Browser URL: `/user-guide/` on the frontend host (local: http://localhost:5173/user-guide/).
Open it through **User guide** in the app footer. Static help is readable without login;
all business data and commands remain protected by the existing application permissions.

The guide is Bengali with exact English UI labels, section navigation, local text search,
responsive layout, system light/dark styling and Print / Save as PDF. Print includes all
sections even when search filters the screen. It has no CDN, extra dependency or API calls.
Vite copies public/user-guide to dist/user-guide on build. Deploy that directory as a static
resource; do not rewrite its index to the SPA. Keep credentials out of this public artifact.

## Coverage map

| Feature | Guide anchors |
| --- | --- |
| 0001 development foundation | configuration, scope |
| UI foundation / 0002 session and shell | login, troubleshooting |
| 0003 organizations / memberships | start, organizations, offboarding, admin |
| 0004 roles / permissions | roles, project-access, walkthrough, admin |
| 0005 account / preferences | account |
| 0006 clients / contacts | clients, admin |
| 0007 people / teams | people, teams, offboarding, admin |
| 0008 projects foundation | projects, project-access, walkthrough, admin |
| 0009 simple resource selection / workforce | people, teams, workforce, walkthrough, admin |

For example, `/user-guide/#roles` opens role configuration directly. There is no separate
Markdown copy of the full guide to keep in sync. Historical planning/verification documents
remain evidence, not competing user instructions.

## Maintenance contract

Update the canonical guide and this map in the same feature/change delivery. Follow P10,
docs/sdd-workflow.md and the SDD task/verification templates. Every chapter needs the actor,
entry point, prerequisites/permissions, exact UI/Admin workflow, realistic placeholder
example, expected result, lifecycle/history rules and recovery steps where relevant.
Check actual code and UI labels; distinguish installed libraries from available business
features. Add guide section links and real checks to the feature verification record.
Keep old anchors stable or provide replacement navigation when reorganizing content.

See [guide delivery verification](verification.md) for current checks and limitations.

Local routing: Vite development and preview middleware explicitly resolve both
`/user-guide` and `/user-guide/` to the public HTML index, preserving query strings.
If a deployed host does not resolve directory indexes, configure that mapping before
its SPA fallback; `/user-guide/index.html` is the direct static-file URL.
