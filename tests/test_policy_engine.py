import pytest

from app.policies import ROLE_POLICIES
from app.policy_engine import PolicyNotFoundError, get_role_policy
from app.schemas import EmployeeRole


def test_get_role_policy_returns_the_matching_policy():
    policy = get_role_policy(EmployeeRole.AUTOMATION_ENGINEER)

    assert policy.role == EmployeeRole.AUTOMATION_ENGINEER
    assert policy.requires_approval is True


def test_get_role_policy_rejects_a_missing_policy(monkeypatch):
    monkeypatch.delitem(
        ROLE_POLICIES,
        EmployeeRole.SUPPORT_ENGINEER,
    )

    with pytest.raises(
        PolicyNotFoundError,
        match="No access policy is defined for role: support_engineer",
    ):
        get_role_policy(EmployeeRole.SUPPORT_ENGINEER)