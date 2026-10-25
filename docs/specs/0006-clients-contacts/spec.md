# 0006 — Clients & Contacts

> Implementation update (2026-10-18): the owner authorized 0005–0008 in App UI and Django Admin. [Delivery decisions and evidence](../0005-0008-delivery.md) supersede the original draft-only labels below. Owner UI/UX acceptance is still pending.

Status: Implemented — owner UI/UX acceptance pending.
Date: 2026-10-18 · Constitution: 1.1 · Implementation authorised: Yes, by the owner on 2026-10-18.
Original planning detail is retained below; the delivery record documents adopted decisions, actual contracts and verification limits.

## Problem and scope
Maintain organization-scoped client organizations and business contacts so projects can reference a stable client without duplicating client records or deleting historical links.

## User stories
- US-1 (P0): As an authorized client manager, I can create and maintain clients and their contacts.
- US-2 (P0): As an authorized reader, I can search active and archived clients within my organization.
- US-3 (P0): As a manager, I can archive a client without erasing project and financial references.

## Acceptance criteria
- **AC-01:** Given client-create permission, valid client details create a stable organization-scoped record; another organization cannot access its ID.
- **AC-02:** Given two organizations, the same client code may exist in both; duplicate code within one organization is rejected consistently.
- **AC-03:** Given client-manage permission, contacts can be added and retired only under a client in the selected organization.
- **AC-04:** Given an existing client is archived, existing references remain readable to authorized users while new project assignment rejects that archived client.
- **AC-05:** Given a bounded search/filter request, results include only permitted clients with deterministic ordering and pagination.
- **AC-06:** Given a stale edit, the update fails without overwriting a newer edit; valid mutations record actor and reason without exposing contact data in general logs.
- **AC-07:** Given a project receives a client summary, it receives immutable DTO fields and cannot write client data directly.
- **AC-08:** Given a client rename, references retain the same ID; a future issued report must use its own snapshot rather than assuming current name is historical.

## Operations, actors and data ownership
The `clients` module owns this feature. Operation/actor mapping is enumerated
in [design.md](design.md). Named permissions are proposed capability keys, not
approved job titles. Organization scope is mandatory for business data; personal
account data is explicitly self-scoped. Personal data must not appear in generic logs.

## Domain invariants
A Client is a customer entity, not a login tenant. Client contacts are not automatically application users. No cascade-delete of business references. Archival prevents new links but does not silently close existing projects. Legal billing identity, taxes and contracts belong to future commercials/billing specs.

## Dependencies
0003 organization scope, 0004 clients permissions. Projects will consume client summary DTOs in 0008.

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
CRM pipeline, leads, client portal login, invoices, contracts, bulk imports, file attachments and custom-field implementation.

## Open decisions — implementation blockers
D-021: confirm client code policy and contact visibility. Recommended human-assigned unique code within organization, name not unique, separate contact read/manage capabilities. Code immutable in first version; correction flow later if needed. No payment/billing detail collected yet.

D-024 covers shared concurrency/revocation semantics; D-012/D-013 cover workload
and retention policy. The owner may revise the proposed slice before implementation.

## Change log
| Date | Change | Authority |
| --- | --- | --- |
| 2026-10-18 | Initial draft for morning review | Owner requested multiple SDD drafts only |
