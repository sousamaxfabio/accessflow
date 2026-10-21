# Security decisions

## Default deny

Only roles in `EmployeeRole` are accepted, every accepted role must have an
explicit policy, and missing application grants mean no access.

## Caller-controlled and system-controlled data

Callers may provide employee facts, action, target role, requester, and reason.
They cannot provide status, approval fields, policy grants, audit events, or
execution results. Pydantic rejects extra input fields.

## Approval boundary

Sensitive grants cannot execute from the intake endpoint. They remain
`pending_approval` until a separate decision request records the reviewer and
comments. The decision endpoint requires a timing-safe API-key comparison, and
a request cannot be decided twice.

## Idempotency

`event_id` is unique in the database. Repeated webhook delivery returns the
original request and does not repeat provisioning.

## MCP boundary

The MCP server exposes only three read operations:

- `get_access_request`
- `list_pending_approvals`
- `explain_role_access`

It exposes no approval or provisioning tool. Mutations stay behind the API and
human-review path.

## Secrets

`.env` is ignored. `.env.example` contains names and safe placeholders only.
Production deployments should use a secret manager and a strong PostgreSQL
password rather than Compose defaults.

## Simulation boundary

Adapters return deterministic local records. They do not possess credentials
for Google Workspace, Slack, Notion, or GitHub and cannot alter real accounts.
