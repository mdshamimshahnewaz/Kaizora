# Project Constitution — [PROJECT NAME]

> **Purpose:** This document records the project's non-negotiable principles, so that every
> later spec, plan and task stays consistent with them. Once written, it is the "ground truth"
> for all other documents.
>
> **Status labels:** CONFIRMED (explicitly approved by the project owner), PROPOSED (suggested,
> not yet approved), OPEN (undecided), DEFERRED (postponed). Only the project owner can promote
> a decision to CONFIRMED. Mark every principle and constraint with one of these labels.

## 1. Mission
[One or two sentences: this project exists to ______.]

## 2. Core Principles (non-negotiable)
List 3–7 principles. Each must be testable/falsifiable — not vague aspiration.

- **P1 — Spec first, with approval gates:** [Rule: work follows Constitution → Spec → Plan → Tasks → Implement & Validate; no stage starts until the owner approves the previous one and asks to proceed; implementation needs a separate explicit instruction]. *Rationale:* [why].
- **P2 — [Name]:** [Rule]. *Rationale:* [why].
- **P3 — [Name]:** [Rule]. *Rationale:* [why].

Examples of good principles: "All user-facing data mutations must be covered by an automated
test", "No feature ships without a written spec first", "Public API responses must never leak
internal IDs".

## 3. Technology Constraints
- Language/Framework: [...]
- Datastore: [...]
- Must avoid: [...]

## 4. Quality Bar
- Test coverage expectation: [...]
- Performance budget (if any): [...]
- Security/compliance requirements: [...]

## 5. Out of Scope (explicitly)
List things this project will deliberately NOT do, to prevent scope creep.
- [...]

## 6. Amendment Process
How/when this constitution can change (e.g., "requires explicit owner approval; each change records its reason, version and date in the amendment log").

---
**Version:** 1.0 · **Last updated:** [date] · **Status:** Draft / Ready for approval / Approved by the project owner

**Amendment log**
- v1.0 ([date]): Initial version.
