import json
import os

from mcp.server import MCPServer

from app.database import SessionLocal, init_database
from app.mcp_queries import (
    explain_role_access_data,
    get_access_request_data,
    list_pending_approval_data,
)


mcp = MCPServer("AccessFlow Read-Only")


@mcp.tool()
def get_access_request(request_id: str) -> dict:
    """Return one access request, its policy, decision, and execution result."""
    with SessionLocal() as session:
        return get_access_request_data(session, request_id)


@mcp.tool()
def list_pending_approvals(limit: int = 25) -> list[dict]:
    """List access requests waiting for a human decision."""
    with SessionLocal() as session:
        return list_pending_approval_data(session, limit)


@mcp.tool()
def explain_role_access(role: str) -> dict:
    """Explain the explicit RBAC grants and approval rule for one role."""
    return explain_role_access_data(role)


@mcp.resource("accessflow://policies/{role}")
def role_policy_resource(role: str) -> str:
    """Read-only RBAC policy resource for an AccessFlow employee role."""
    return json.dumps(explain_role_access_data(role), indent=2)


if __name__ == "__main__":
    init_database()
    if os.getenv("ACCESSFLOW_MCP_TRANSPORT") == "streamable-http":
        mcp.run(
            transport="streamable-http",
            stateless_http=True,
            json_response=True,
        )
    else:
        mcp.run()
