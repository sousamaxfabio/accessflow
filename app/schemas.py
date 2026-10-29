from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AccessAction(str, Enum):
    ONBOARD = "onboard"
    CHANGE_ROLE = "change_role"
    OFFBOARD = "offboard"


class Department(str, Enum):
    SUPPORT = "support"
    ENGINEERING = "engineering"
    OPERATIONS = "operations"
    FINANCE = "finance"
    HUMAN_RESOURCES = "human_resources"


class EmployeeRole(str, Enum):
    SUPPORT_ENGINEER = "support_engineer"
    AUTOMATION_ENGINEER = "automation_engineer"
    OPERATIONS_MANAGER = "operations_manager"
    FINANCE_ANALYST = "finance_analyst"
    HR_SPECIALIST = "hr_specialist"


class ApprovalDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


class AccessRequestCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    event_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )
    employee_id: str = Field(
        min_length=1,
        max_length=50,
        pattern=r"^[A-Za-z0-9-]+$",
    )
    employee_name: str = Field(min_length=2, max_length=100)
    department: Department
    action: AccessAction
    target_role: EmployeeRole | None = None
    requested_by: str = Field(min_length=3, max_length=100)
    reason: str = Field(min_length=10, max_length=500)

    @model_validator(mode="after")
    def validate_target_role(self) -> "AccessRequestCreate":
        role_required_actions = {
            AccessAction.ONBOARD,
            AccessAction.CHANGE_ROLE,
        }

        if self.action in role_required_actions and self.target_role is None:
            raise ValueError("target_role is required for onboarding and role changes")

        if self.action == AccessAction.OFFBOARD and self.target_role is not None:
            raise ValueError("target_role must not be provided for offboarding")

        return self


class ApprovalDecisionCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    decision: ApprovalDecision
    reviewer: str = Field(min_length=2, max_length=100)
    comments: str = Field(min_length=3, max_length=500)
