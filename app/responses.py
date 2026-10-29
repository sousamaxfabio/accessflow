from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.policies import AccessGrant
from app.schemas import AccessAction, ApprovalDecision, Department, EmployeeRole


class AccessRequestStatus(str, Enum):
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class AccessRequestAccepted(BaseModel):
    request_id: UUID
    event_id: str
    status: AccessRequestStatus
    requires_approval: bool
    duplicate: bool = False


class AccessRequestDetail(AccessRequestAccepted):
    employee_id: str
    employee_name: str
    department: Department
    action: AccessAction
    target_role: EmployeeRole | None
    requested_by: str
    reason: str
    policy: list[AccessGrant]
    execution_results: list[dict[str, Any]]
    approval_decision: ApprovalDecision | None
    approval_reviewer: str | None
    approval_comments: str | None
    created_at: datetime
    updated_at: datetime


class AuditEventView(BaseModel):
    id: int
    request_id: UUID
    event_type: str
    details: dict[str, Any]
    created_at: datetime
