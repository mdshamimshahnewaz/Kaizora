# সকালে পড়ার গাইড — Basic module SDD batch

তারিখ: 2026-10-18। ছয়টি feature, প্রতিটিতে চারটি document।
**সবগুলো draft; application code implement করা হয়নি।** নতুন business rules,
API shapes ও models প্রস্তাবিত। তোমার approval বা test result বানিয়ে লেখা হয়নি।

## কোনটা আগে পড়বে

প্রথমে প্রতিটি `spec.md` পড়লেই scope ও business decisions বুঝবে। এরপর সংশ্লিষ্ট
`design.md`-এ data/API/interface, `tasks.md`-এ future কাজ এবং `verification.md`-এ
কীভাবে পরীক্ষা করা হবে দেখবে।

| ক্রম | Feature | কী সিদ্ধান্ত নেবে |
| --- | --- | --- |
| 1 | [0003 Organizations & Membership](../specs/0003-organizations-membership/spec.md) | এক user একাধিক organization? কে organization বানাবে? member যোগ করার প্রথম ব্যবস্থা কী? |
| 2 | [0004 Roles & Permissions](../specs/0004-roles-permissions/spec.md) | প্রথম roles ও permission matrix; কে কাকে কতটুকু permission দিতে পারবে? |
| 3 | [0005 Account & Preferences](../specs/0005-account-preferences/spec.md) | নাম/theme/timezone self-edit হবে? email/password এই slice-এর বাইরে থাকবে? |
| 4 | [0006 Clients & Contacts](../specs/0006-clients-contacts/spec.md) | client code ও contact তথ্যের access policy |
| 5 | [0007 People & Teams](../specs/0007-people-teams/spec.md) | login ছাড়া resource, একাধিক team ও login-resource linkage |
| 6 | [0008 Projects Foundation](../specs/0008-projects-foundation/spec.md) | private project, client ছাড়া internal project, initial manager ও lifecycle |

## আমার প্রস্তাব — এখনো অনুমোদিত নয়

1. Data model একাধিক organization membership সমর্থন করবে; UI-তে একবারে একটি selected organization।
2. প্রথম release-এ operator organization/first owner বানাবে, existing user-কে যোগ করা যাবে। Email invitation পরের আলাদা feature।
3. Owner একটি protected capability; configurable roles দিয়ে অন্য permissions দেওয়া হবে। Staff হওয়া মানেই সব business data access নয়।
4. Account-এ নিজের নাম, theme ও timezone edit; password/email/security flow আলাদা spec।
5. Client code organization-এর মধ্যে unique; contact data আলাদা permission-এ।
6. Resource profile login ছাড়াও থাকতে পারবে। Team membership কোনো project permission বা billing status নয়।
7. Project private-by-default; internal project-এ client optional। Project access ও staffing allocation আলাদা।

## Dependency ও implementation order

0003-এর scope/owner foundation আগে; তারপর 0004-এর policy service। 0003-এর general membership-manager UI এবং endpoints policy wiring না হওয়া পর্যন্ত deny করবে। এই দুটি পাশাপাশি contract review করতে হবে; deployment order মানেই circular imports নয়।

তারপর 0005, 0006 ও 0007 review/implementation আলাদা slice হতে পারে। 0008-এর জন্য
0003/0004 ও 0006 দরকার। Resource allocation দরকার হওয়ার আগে 0007-কে project access-এর বাধ্যতামূলক dependency বানানো হয়নি।

Proposed dependency direction: clients/resources/projects → identity permission interface
→ organizations scope interface। Projects → clients summary/locking interface।
Organizations policy port composition root-এ identity implementation দিয়ে wire হবে;
organizations identity-কে import করবে না। Public command-এ permission bypass flag থাকবে না।

## কী এই batch-এ নেই

Work items, allocation/replacement, time approvals, operational queue, billing, report
builder, customization implementation, email delivery এবং global audit explorer পরে।
Current drafts কেবল per-module change events specify করেছে; full audit platform নয়।
No custom-fields JSON shortcut: scope/type/filter/history design D-009-এ আলাদা হবে।

## Review findings and disposition

- **Resolved in drafts:** identity/organization permission checks could create an import
  cycle. Use an organizations-owned policy port with fail-closed default and composition
  wiring; ordinary commands must validate policy rather than accept a caller boolean.
- **Resolved in drafts:** project creation could race with client archival. Add a clients
  public locking validation contract within the owning project transaction; archival
  does not close existing projects. Projects never writes client tables.
- **Resolved in drafts:** resource/login linkage could relabel history. Preserve stable
  resource IDs and dated link events; future time records store worker and actor separately.
- **Unresolved:** concrete role catalog/delegation and initial project manager are product
  choices (D-019/D-023). Do not implement from guessed employee/manager roles.
- **Unresolved:** D-024 revocation linearization and final serializer examples need refinement
  before code. Latency targets and retention are proposals, not guarantees.

## Readiness and verification record

Planning confidence: module boundaries and existing-stack fit are grounded in local code;
product-policy confidence remains conditional on the decisions above. These are review
artifacts, not six automatically executable approved plans. No application checks ran.
A separate specialist `ce-doc-review` invocation has not run; the review above is an
inline consistency review, not an independent review receipt.

Documentation-only validation: see the recorded result below after link/AC checks.
No server, database migration, dependency installation, application code or generated
schema was changed. Morning next action is owner review, not automatic implementation.

### Executed documentation check

PASS: 6 feature folders, 24 feature documents, 48 unique-per-feature acceptance criteria mapped to design and planned verification; 59 relative links valid across 27 reviewed files. All 48 acceptance results remain Not executed; no implementation tasks checked complete.

Follow-up consistency corrections: explicit client locking interface, project-role scope
restrictions, prospective team-date rules and atomic initial project-manager creation.
These are proposed design corrections, not application changes or passed feature tests.

## Approval update — 2026-10-18

Owner approved feature 0003 (“OKay 003 features approved”). Its specification and
D-018 product recommendations are now approved, superseding the original all-draft
status above for that spec only. Design/tasks remain drafts; application implementation
and executed verification remain unauthorised/unperformed. Other features remain drafts.

## 0003 implementation update — 2026-10-18

The owner subsequently instructed “Please implement”. 0003 has now been implemented,
including additive migration applied to the configured database. The original planning-only
notes above describe the prior state. See 0003 verification.md for current evidence and
limits; general membership management still awaits 0004 policy. Other five features remain
drafts and no owner acceptance of completed implementation has been recorded.
