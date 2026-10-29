from enum import Enum

from pydantic import BaseModel, ConfigDict, computed_field

from app.schemas import EmployeeRole


class ApplicationName(str, Enum):
    GOOGLE_WORKSPACE = "google_workspace"
    SLACK = "slack"
    NOTION = "notion"
    GITHUB = "github"


class AccessGrant(BaseModel):
    model_config = ConfigDict(frozen=True)

    application: ApplicationName
    permission: str
    resource: str
    sensitive: bool = False


class RolePolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: EmployeeRole
    grants: tuple[AccessGrant, ...]

    @computed_field
    @property
    def requires_approval(self) -> bool:
        return any(grant.sensitive for grant in self.grants)


ROLE_POLICIES: dict[EmployeeRole, RolePolicy] = {
    EmployeeRole.SUPPORT_ENGINEER: RolePolicy(
        role=EmployeeRole.SUPPORT_ENGINEER,
        grants=(
            AccessGrant(
                application=ApplicationName.GOOGLE_WORKSPACE,
                permission="standard_user",
                resource="organization",
            ),
            AccessGrant(
                application=ApplicationName.SLACK,
                permission="member",
                resource="support_channels",
            ),
            AccessGrant(
                application=ApplicationName.NOTION,
                permission="reader",
                resource="support_knowledge_base",
            ),
        ),
    ),
    EmployeeRole.AUTOMATION_ENGINEER: RolePolicy(
        role=EmployeeRole.AUTOMATION_ENGINEER,
        grants=(
            AccessGrant(
                application=ApplicationName.GOOGLE_WORKSPACE,
                permission="standard_user",
                resource="organization",
            ),
            AccessGrant(
                application=ApplicationName.SLACK,
                permission="member",
                resource="engineering_and_automation_channels",
            ),
            AccessGrant(
                application=ApplicationName.NOTION,
                permission="editor",
                resource="automation_workspace",
            ),
            AccessGrant(
                application=ApplicationName.GITHUB,
                permission="write",
                resource="automation_repositories",
                sensitive=True,
            ),
        ),
    ),
    EmployeeRole.OPERATIONS_MANAGER: RolePolicy(
        role=EmployeeRole.OPERATIONS_MANAGER,
        grants=(
            AccessGrant(
                application=ApplicationName.GOOGLE_WORKSPACE,
                permission="standard_user",
                resource="organization",
            ),
            AccessGrant(
                application=ApplicationName.SLACK,
                permission="member",
                resource="operations_and_incident_channels",
                sensitive=True,
            ),
            AccessGrant(
                application=ApplicationName.NOTION,
                permission="editor",
                resource="operations_workspace",
            ),
            AccessGrant(
                application=ApplicationName.GITHUB,
                permission="read",
                resource="operations_repositories",
            ),
        ),
    ),
    EmployeeRole.FINANCE_ANALYST: RolePolicy(
        role=EmployeeRole.FINANCE_ANALYST,
        grants=(
            AccessGrant(
                application=ApplicationName.GOOGLE_WORKSPACE,
                permission="standard_user",
                resource="organization",
            ),
            AccessGrant(
                application=ApplicationName.SLACK,
                permission="member",
                resource="finance_private_channel",
                sensitive=True,
            ),
            AccessGrant(
                application=ApplicationName.NOTION,
                permission="reader",
                resource="finance_workspace",
                sensitive=True,
            ),
        ),
    ),
    EmployeeRole.HR_SPECIALIST: RolePolicy(
        role=EmployeeRole.HR_SPECIALIST,
        grants=(
            AccessGrant(
                application=ApplicationName.GOOGLE_WORKSPACE,
                permission="standard_user",
                resource="organization",
            ),
            AccessGrant(
                application=ApplicationName.SLACK,
                permission="member",
                resource="hr_private_channel",
                sensitive=True,
            ),
            AccessGrant(
                application=ApplicationName.NOTION,
                permission="editor",
                resource="hr_workspace",
                sensitive=True,
            ),
        ),
    ),
}
