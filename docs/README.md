# Kaizora documentation

Updated: 2026-10-18. This is the entry point for specification-driven development.

## Read order and authority
User instructions define the authorised scope. Read [constitution](constitution.md),
[architecture](architecture.md), [decisions](decisions.md), then the relevant feature.
Shared conventions govern new work; they do not claim that future functionality exists.
If documents conflict with code, record the discrepancy and resolve it before dependent work.

| Document | Purpose |
| --- | --- |
| [End-user guide](user-guide/README.md) | Browser guide, configuration examples and UI/Admin workflows |
| [Constitution](constitution.md) | Stable engineering and domain principles |
| [Architecture](architecture.md) | Boundaries, ownership and deployment model |
| [Decisions](decisions.md) | Confirmed direction, proposals and unresolved choices |
| [Technology stack](tech-stack.md) | Actual dependency sources and change policy |
| [API conventions](api-conventions.md) | HTTP contracts and compatibility |
| [Frontend API client](frontend-api-client.md) | Browser integration and session handling |
| [Frontend UI rules](frontend-ui-rules.md) | Shared components, themes and accessibility |
| [SDD workflow](sdd-workflow.md) | Stages, authorisation and change control |
| [SDD guide](sdd-guide.md) | Practical instructions for owners and contributors |
| [Feature index](specs/README.md) | Status and evidence for each feature |
| [Templates](../sdd-templates/README.md) | Reusable feature documents and prompts |

[Module inventory](architecture/modules.md) and [ADRs](architecture/0001-modular-monolith.md)
remain authoritative specialised references. [OpenAPI](api/openapi.yaml) is generated
from the implemented API. Frontend visual details live in
[design-system.md](../frontend/docs/design-system.md).

`example-sdd/` is Timely reference material, not active Kaizora instructions. It is
preserved unchanged. Kaizora uses React/Vite, not Next.js. No Timely approvals,
provider settings or implementation evidence transfer to this project.
