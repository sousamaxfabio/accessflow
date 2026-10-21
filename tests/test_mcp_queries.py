import asyncio

import pytest
from mcp import Client

from app.mcp_queries import explain_role_access_data
from mcp_server import mcp


def test_mcp_policy_explanation_is_structured_and_read_only():
    policy = explain_role_access_data("automation_engineer")

    assert policy["role"] == "automation_engineer"
    assert policy["requires_approval"] is True
    assert {grant["application"] for grant in policy["grants"]} == {
        "google_workspace",
        "slack",
        "notion",
        "github",
    }


def test_mcp_policy_explanation_rejects_unknown_roles():
    with pytest.raises(ValueError, match="Unknown role 'super_admin'"):
        explain_role_access_data("super_admin")


def test_mcp_exposes_only_the_intended_read_only_tools():
    async def list_tool_names() -> set[str]:
        async with Client(mcp) as client:
            result = await client.list_tools()
            return {tool.name for tool in result.tools}

    assert asyncio.run(list_tool_names()) == {
        "get_access_request",
        "list_pending_approvals",
        "explain_role_access",
    }
