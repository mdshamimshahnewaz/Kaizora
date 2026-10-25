# 0005 — Account & Preferences

> Implementation update (2026-10-18): the owner authorized 0005–0008 in App UI and Django Admin. [Delivery decisions and evidence](../0005-0008-delivery.md) supersede the original draft-only labels below. Owner UI/UX acceptance is still pending.

Status: Implemented — owner UI/UX acceptance pending.
Date: 2026-10-18 · Constitution: 1.1 · Implementation authorised: Yes, by the owner on 2026-10-18.
Original planning detail is retained below; the delivery record documents adopted decisions, actual contracts and verification limits.

## Problem and scope
Allow each signed-in user to view and update a limited personal profile and presentation preferences without editing organization-controlled data or weakening authentication.

## User stories
- US-1 (P0): As a signed-in user, I can update my own name and see account information.
- US-2 (P1): As a user, I can keep theme and timezone preferences across sessions.
- US-3 (P0): As an operator, I can keep identity and membership fields outside self-service editing.

## Acceptance criteria
- **AC-01:** Given an active session, reading my account returns only my own permitted fields; no arbitrary user identifier can retrieve someone else.
- **AC-02:** Given valid first/last name updates, saving changes the displayed name after reload without changing username, email, roles or active status.
- **AC-03:** Given invalid timezone or theme values, saving fails with field errors and retains previous valid preferences.
- **AC-04:** Given a stale profile version, saving returns conflict and the UI preserves unsaved input for review.
- **AC-05:** Given no personal timezone override, the effective timezone follows the selected organization, falling back to the configured application timezone outside an organization.
- **AC-06:** Given a preference change, date rendering changes but stored work dates, time durations, rates and financial values do not.
- **AC-07:** Given an anonymous request or missing CSRF on update, access is denied and no data changes.
- **AC-08:** Given successful updates, a fresh session snapshot and account menu reflect the new name; failed updates do not falsely appear saved.

## Operations, actors and data ownership
The `identity` module owns this feature. Operation/actor mapping is enumerated
in [design.md](design.md). Named permissions are proposed capability keys, not
approved job titles. Organization scope is mandatory for business data; personal
account data is explicitly self-scoped. Personal data must not appear in generic logs.

## Domain invariants
Account profile is global to the login identity; resource/employment profiles are organization-owned and separate. Proposed editable fields are first_name and last_name only. Theme options are light/dark/system; timezone may be null to inherit. Current theme behaviour is preserved until server preferences load, then explicit saved preference wins. No financial data is recalculated because display preferences changed.

## Dependencies
0002 session lifecycle; organization context from 0003 for effective preference fallback.

## Non-functional requirements
Permission refusal must occur server-side and stale edits must not overwrite newer data.
Lists must be bounded; latency/dataset targets need D-012 approval. Screens must be
keyboard-operable with visible focus, labels and announced errors; use existing themes.
Retention and audit access require D-013 resolution for production. Business dates and
timestamps have different semantics; user timezone never rewrites stored work.

## Edge cases
Cross-tenant IDs, inactive actor, concurrent edits, duplicate submission, empty lists,
network loss after a write, stale organization requests and archived references.
On an uncertain mutation outcome refresh authoritative state before retry; do not
blindly replay an action. Feature-specific cases are captured in ACs above.

## Out of scope
Password/email/username changes, MFA, avatar uploads, account deletion, organization settings, employment data and session revocation UI.

## Open decisions — implementation blockers
D-020: confirm self-editable fields and whether preferences should follow the user across devices. Recommended first/last name + theme/timezone only. Username/email changes, password change/reset and session-management screens require a separate security feature. Localization/date-format selection is deferred; do not create a language dropdown with no translated UI.

D-024 covers shared concurrency/revocation semantics; D-012/D-013 cover workload
and retention policy. The owner may revise the proposed slice before implementation.

## Change log
| Date | Change | Authority |
| --- | --- | --- |
| 2026-10-18 | Initial draft for morning review | Owner requested multiple SDD drafts only |
