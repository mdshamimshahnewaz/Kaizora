# Kaizora delivery instructions

Read docs/constitution.md and docs/sdd-workflow.md before feature work.

## User guide is required
Owner instruction (2026-10-18): complete each user-facing feature with its end-user
guide, including configuration and examples for App UI and Django Admin where applicable.
Update frontend/public/user-guide/index.html (served at /user-guide/) and the coverage
map in docs/user-guide/README.md. Link the sections and actual verification in the
feature verification.md. Cover permissions, prerequisites, fields, steps, outcomes,
history and failure recovery; do not claim future features or expose real secrets.
Do not mark user-facing work complete without this documentation. Internal-only changes
must record why no user-guide update is applicable. Follow the existing UI/Admin delivery
learning in docs/solutions/workflow-issues/complete-features-through-ui-and-admin.md.
