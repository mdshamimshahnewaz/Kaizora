# Using Kaizora SDD

Start at [documentation index](README.md). The [workflow](sdd-workflow.md) defines
stages and authority; [templates](../sdd-templates/README.md) supply the document shape.

## Start a feature
Describe the users, problem, desired outcome, exclusions and examples. State whether
you want a spec only or implementation too. Use the feature prompt. The contributor
checks the feature index, assigns the next unused four-digit ID, and writes a spec.
Unresolved roles, business rules or historical behaviour remain explicit questions.
Do not start implementing dependent behaviour by guessing the answer.

## Review a spec
Check that each acceptance criterion is observable, permissions include refusal cases,
and real examples cover edge cases. For allocation/billing, changing today's roster
must not rewrite yesterday's work. For custom fields, ask how filtering, permissions,
retired fields and historical reports behave. Exclude unrelated work explicitly.

## Review design and tasks
Check module ownership and interfaces, transaction boundaries, actor/tenant checks,
API contracts, migration/rollback, UI states and performance workload. Confirm every
AC maps to tasks and validation. Tasks need dependencies and concrete done conditions.
Review important tradeoffs; file size is not a measure of design quality.

## Verify and close
Read verification evidence, not just the count of passing tests. A mocked API test
is not an end-to-end browser test. Partial/unrun checks must stay visible. Ask for
missing checks or explicitly accept a documented limitation. Owner acceptance can
then close the feature; deployment still needs its own requirements.

## Resume in another session
Read constitution, decisions, feature index and the active feature's four documents.
Find the last executed evidence and next incomplete task. Check current code before
assuming an old result still applies. Do not restart completed work or fabricate an
approval from a status label.

## Prompt examples
- “Write the specification for project membership; do not implement yet.”
- “Implement this reviewed feature, including design, tasks and verification.”
- “Change this acceptance criterion as follows and update affected contracts/tests.”
- “Show outstanding decisions and unverified acceptance criteria.”

## Reuse in another project
Reuse the document structure, not Kaizora's business policy, credentials, approvals,
stack assumptions or evidence. Timely's Next.js/BFF and external providers are not
part of Kaizora. Keep project-specific decisions explicit.
