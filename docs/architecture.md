# Architecture

```mermaid
flowchart LR
    HR[HR or manager] --> N8N[n8n intake]
    N8N --> API[FastAPI]
    API --> VALIDATE[Pydantic validation]
    VALIDATE --> POLICY[RBAC policy engine]
    POLICY --> DB[(PostgreSQL)]
    POLICY -->|sensitive| APPROVAL[Human approval]
    POLICY -->|standard| ADAPTERS[Safe SaaS adapters]
    APPROVAL -->|approved| ADAPTERS
    APPROVAL -->|rejected| DB
    ADAPTERS --> DB
    MCP[Read-only MCP server] --> DB
    MCP --> POLICY
```

## Trust boundaries

1. Incoming JSON is untrusted and validated with Pydantic.
2. Callers choose a role, never individual application permissions.
3. RBAC policies are explicit and default-deny.
4. Sensitive grants stop at `pending_approval`.
5. Only the HTTP approval endpoint changes approval state; MCP is read-only.
6. SaaS adapters are local simulations and cannot change real accounts.
7. Every policy, approval, and provisioning transition is audited.

## State machine

```mermaid
stateDiagram-v2
    [*] --> submitted
    submitted --> completed: standard access or offboarding
    submitted --> pending_approval: sensitive access
    pending_approval --> rejected: reviewer rejects
    pending_approval --> approved: reviewer approves
    approved --> executing
    executing --> completed
    executing --> failed: adapter failure
```

The current simulated adapters return deterministic successes. The `failed`
state is reserved for replacing them with real integrations.
