from app.policies import ApplicationName, ROLE_POLICIES
from app.schemas import EmployeeRole


def test_support_engineer_policy_uses_least_privilege():
    policy = ROLE_POLICIES[EmployeeRole.SUPPORT_ENGINEER]

    granted_applications = {
        grant.application for grant in policy.grants
    }

    assert granted_applications == {
        ApplicationName.GOOGLE_WORKSPACE,
        ApplicationName.SLACK,
        ApplicationName.NOTION,
    }
    assert ApplicationName.GITHUB not in granted_applications
    assert policy.requires_approval is False


def test_automation_engineer_policy_requires_approval():
    policy = ROLE_POLICIES[EmployeeRole.AUTOMATION_ENGINEER]

    github_grant = next(
        grant
        for grant in policy.grants
        if grant.application == ApplicationName.GITHUB
    )

    assert github_grant.permission == "write"
    assert github_grant.resource == "automation_repositories"
    assert github_grant.sensitive is True
    assert policy.requires_approval is True