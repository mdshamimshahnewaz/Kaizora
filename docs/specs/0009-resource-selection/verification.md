# Verification — 0009 simple resource selection

2026-10-18. Implementation authorized; owner UI/UX acceptance pending.

## Acceptance evidence

| AC | Result | Evidence |
| --- | --- | --- |
| AC1 direct member selection | Passed | API tests create/reuse one resource, reject overlapping team assignment and roll back identity creation for invalid dates. UI tests submit membership ID directly without person form. |
| AC2 no-login workforce | Passed | API/Admin tests add no-login and member workers without creating users/access grants, end with reason/version and preserve rows. Project reader cannot write. |
| AC3 search / tenant isolation | Passed | API bounded name/username search, wrong-tenant/suspended member denial. UI server-search test ignores a late old response and uses keyboard selection. |
| AC4 preservation | Passed | Additive migration only. Tests reject retired identity duplication and ended-link auto-recreation, stale end versions and archived project additions. Existing history/isolation regression suite retained. |
| AC5 UI/Admin/guide | Passed with browser limits below | Actual Admin POST tests for direct member resources, team member assignment and no-login project worker add/end. Guide updated in same delivery. |

## Executed checks

- Initial attempted historical test service on port 55432 was offline; no test result claimed for that run. Used the configured PostgreSQL service with Django's separate test database, without modifying live business records.
- Final full backend regression: **65 passed**. Focused selection suite: **7 passed**, including name-only no-login creation and retired-identity protection.
- Full frontend regression: 54 passed across 10 files. One existing project picker test was adapted from inline button to portalled option; its creation-payload assertion remains unchanged.
- Tests caught an empty accessible search name caused by cmdk aria-labelledby overriding the input label; corrected the Command label. Keyboard/server-search test now passes.
- TypeScript caught an unsupported test selector option; removed it. Frontend production build subsequently passed. ESLint, Ruff and module boundaries passed; 3 boundary checker tests passed.
- OpenAPI validated without warnings and TypeScript types regenerated. Django check passed; migration drift absent. Additive projects.0002_projectworker applied to configured local database. No existing identities/assignments were migrated or erased.
- Browser read-only check: opened People → Add existing member; searched the actual organization member dropdown and inspected desktop layout. No live save or example records created. Screenshot: /tmp/kaizora-member-search.jpg.

## User guide

[Guide coverage](../../user-guide/README.md): `/user-guide/#people`, `#teams`, `#workforce`, `#admin`, `#walkthrough`. Member selection is the default path; no-login creation needs only a name, with optional immutable code. Ended links require explicit relinking. The guide distinguishes workforce from application access and explicitly defers tasks/time/financial tracking.

## Review and limitations

Cross-module consumers use public interfaces. Trusted worker resolution requires an owning command to authorize and hold the shared organization lock; commands revalidate current scopes. Member identity is never inferred by matching names. ProjectWorker stores the assignment-time name; user/resource rename does not rewrite it.

Admin search filters eligible choices already loaded in the form; web pickers use server-side bounded search. Large Admin selectors remain a scaling limitation. Browser visual review covered the member dropdown, not a full persisted end-to-end journey, mobile viewport or every Admin form. Automated API/Admin/UI checks provide mutation evidence. No production performance claim or owner acceptance is implied.

Workforce is a roster only. Task/time entry by TL/PM, capacity/billability, replacements and financial reporting remain future features. No server was started, no commit/PR/publication made. Independent diff review cannot be established against this workspace's absent committed Git baseline; manual source/permission review and tests are the recorded evidence.

Final guide check: all fragment anchors resolve, workforce search finds the chapter, and the built static guide matches the canonical HTML. Admin end-assignment help explicitly states that login/project access is unchanged.
