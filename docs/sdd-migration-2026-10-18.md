# SDD documentation adaptation — 2026-10-18

Authority: owner requested adapting the fuller Timely documentation system to Kaizora.
Scope: documentation only. Runtime code, dependencies, environment and databases unchanged.

## Delivered
- Expanded constitution and architecture; decision register with provenance and open items.
- Stack, API, frontend client and UI rules grounded in current manifests/settings/client.
- SDD workflow/guide, feature index and eight reusable template/prompt documents.
- Preserved existing feature documents, validation history and all Timely references.
- Reconciled stale login descriptions in root README and architecture ADR.

## Deliberate adaptations
React/Vite SPA and shared browser DRF client replace Timely's Next.js/BFF assumptions.
Retained `docs/specs/NNNN-slug/`, `design.md` and `verification.md` to avoid duplicated
sources. Separate staged requests from already-authorised implementation; provide a
small-change path. No imported approval records, SSO requirements or external vendors.

## Verification
Executed local link check: 23 Markdown files, 59 relative links, zero missing targets.
Required documentation/template files are present. Two template-only destination links
were converted to code references so templates also validate before being copied. Current API/client
claims were compared with settings.py, frontend package.json, backend requirements.in
and auth client sources. Generated API files were not edited. No application tests,
build, database operations or servers are needed for this documentation-only change.
This workspace has no functioning Git repository, so no Git diff/commit is available.
Owner acceptance of this delivered documentation has not yet been recorded.
