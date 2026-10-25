# API conventions

Authority: [constitution](constitution.md), [architecture](architecture.md).
Current contracts: [OpenAPI](api/openapi.yaml). Future policies below are design
requirements, not claims of existing middleware or business endpoints.

## Implemented baseline
- Versioned `/api/v1/` endpoints with trailing slash, JSON responses and snake_case fields.
- Shared web/mobile contract; native mobile auth remains deferred.
- Default DRF permission is authenticated; health/session/login and idempotent logout
  have explicit endpoint-specific behaviour. Session snapshot returns 200 with
  `user: null` for anonymous callers; do not replace that with an assumed 401.
- Unsafe session requests require CSRF. Login/logout explicitly enforce CSRF even
  for anonymous calls. Login can return 400, 403 or 429; logout success is 204.
- DRF SessionAuthentication may return 403 for unauthenticated access. Clients must
  follow the documented endpoint contract, not infer that every 403 means expiry.
- DRF default page-number pagination is configured at 50 rows. No business list
  endpoints, maximum-page-size convention or custom-field filtering exist yet.
- Errors currently use DRF endpoint/serializer shapes (including `detail` and field
  errors), not a globally implemented custom envelope or request-ID middleware.

## Requirements for new contracts
Each design defines method/path, actor/permissions, request, response, status codes,
field errors, pagination, allowed filters/sorts, concurrency and idempotency where
needed. Use bounded lists; choose cursor pagination for large changing streams when
justified. Define maximum sizes and deterministic sorting per endpoint. Reject invalid
filter values; document treatment of unknown parameters. Apply tenant and field
permissions to list results, aggregates, exports and custom-field predicates alike.

Use ISO 8601 timestamps with an explicit offset; define business dates and reporting
timezone separately. Backend currently uses USE_TZ and Asia/Dhaka as its configured
timezone. Use decimal representations and explicit currency/rounding policy for money;
do not introduce float-based financial contracts. Identity currently uses UUIDs;
other entity identifiers must be specified, not assumed.

Server validation is authoritative. Generic failures must not leak SQL, secrets,
stack traces or cross-tenant existence. Specify conflicts and stale-write handling.
A common error envelope/request IDs remain D-016, requiring a separate compatible
change. Do not silently change existing error semantics.

## Evolution and verification
Update feature design before changing a contract. Generate OpenAPI from DRF, then
regenerate frontend types; never hand-edit generated files. Run schema validation,
TypeScript and relevant endpoint/client tests. Assess old-client compatibility;
breaking changes need an explicit version/migration strategy. Generation commands
are in the [root README](../README.md#update-api-contract).
