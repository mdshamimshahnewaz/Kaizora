# NNNN — Feature name

Status: Draft · Constitution: 1.1 · Owner approval: Not recorded

## Summary and users
Problem, outcome and WHY. Keep technical implementation in design.md.

## Stories and priorities
- US-1 (P0): As [actor], I want [capability] so that [benefit].

## Acceptance criteria
- AC-1: Given [context], when [operation], then [observable outcome].
- AC-2: Given [unauthorised actor/scope], when [operation], then [refusal].

## Operations and data
| Business operation | Allowed actor/scope | Data owner/sensitivity | AC |
| --- | --- | --- | --- |
| Fill in | Resolve roles; do not guess | Include retention/freshness | AC-1 |

## Domain invariants
Historical dates, removal/replacement, billability, correction, attribution and
custom-field behaviour. Include concrete examples, or explain non-applicability.

## Non-functional requirements
Measurable workload/latency, security/audit, accessibility, timezone and retention.
Unknown targets are OPEN decisions, not invented performance claims.

## Edge cases and dependencies
Empty/error states, concurrency, external failures and dependent decisions/features.

## Out of scope
Explicit exclusions.

## Open questions
Decision IDs, owner/input needed and whether implementation is blocked.

## Change log
| Date | Change and affected AC | Reason | User direction / approval |
| --- | --- | --- | --- |
