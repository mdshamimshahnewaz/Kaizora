# Concepts

Shared domain vocabulary for this project — entities, named processes, and status concepts with project-specific meaning. Seeded with core domain vocabulary, then accretes as ce-compound and ce-compound-refresh process learnings; direct edits are fine. Glossary only, not a spec or catch-all.

## Organization

A tenant boundary within which memberships and business permissions are scoped. A user can belong to more than one organization through separate memberships.

## Membership

The persistent relationship between a user and an organization. Access-status changes update that relationship and record its history rather than replacing its identity.

## Organization owner

A membership carrying reserved ownership authority. Ownership transfer requires an active owner and an active target member; it changes the ownership designation and records the transition.

## Provisioning operator

An active identity authorized to create an organization and designate its first owner. Provisioning authority does not itself grant membership in the organization created.
