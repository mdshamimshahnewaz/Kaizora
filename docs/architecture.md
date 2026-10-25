# Kaizora architecture

Updated: 2026-10-18. Read with [constitution](constitution.md) and
[ADR 0001](architecture/0001-modular-monolith.md).

## System shape
React + TypeScript + Vite SPA → `/api/v1/` DRF adapters → owning module's use cases
and public interfaces → PostgreSQL. Django Admin is an operator surface.
React Router owns browser routes. There is no Next.js runtime, BFF, server component,
server action or frontend database layer. Vite proxies `/api` locally; production
must serve SPA deep links and reverse-proxy Django under the same origin.

## Module rules
- [Module inventory](architecture/modules.md) defines owners and planned capabilities.
- `interfaces.py` is the cross-module entry point. Return typed immutable DTOs;
  do not expose models, QuerySets or another module's private services.
- Each feature declares one-directional dependencies. Resolve cycles using interface
  inversion or an explicit orchestrating use case rather than hidden imports.
- Identify the transaction owner and atomic boundary for every command. Foreign keys
  do not grant cross-module write access. Avoid network I/O inside DB transactions.
- Read projections need a documented owner, source, freshness and access policy.
  Reports cannot infer historical membership from the current roster.
- Module extraction is a future option, not automatic. No internal HTTP, message bus,
  Celery or outbox without an actual requirement and design.

## Contract and security boundaries
DRF validates transport input; domain use cases enforce invariants and permissions.
Frontend validation aids users but never grants authority. Admin must invoke domain
use cases when business actions are introduced. Identity owns session authentication;
organisation membership and object permissions require their own feature spec.
Web uses CSRF-protected Django sessions. Native mobile authentication is deferred;
shared API design does not mean mobile sign-in is implemented.

## Current enforcement and limits
`scripts/check_boundaries.py` checks ordinary static imports. It does not detect raw
SQL, dynamic imports or model-registry access; review must check these escape routes.
Identity, system and organizations are installed domain apps. Reserved module directories are
not implemented features. Generated OpenAPI and TypeScript types exist today.

## Every feature design must state
Module/data ownership, dependencies, public interface signatures, immutable DTOs,
actor/scope checks, transaction ownership, API changes, schema/index/migration impact,
historical effects, custom-field effects and verification. Mark non-applicable items
with a reason. External adapters specify credentials, timeout, retry/idempotency,
rate limits and reconciliation without copying vendor logic into the frontend.
