import pytest
from pydantic import ValidationError

from app.schemas import (
    AccessAction,
    AccessRequestCreate,
    EmployeeRole,
)


def test_valid_onboarding_request_is_accepted():
    request = AccessRequestCreate(
        event_id="evt-001",
        employee_id="EMP-1042",
        employee_name="  Alice Morgan  ",
        department="support",
        action="onboard",
        target_role="support_engineer",
        requested_by="manager@example.test",
        reason="New employee starting on Monday",
    )

    assert request.action == AccessAction.ONBOARD
    assert request.target_role == EmployeeRole.SUPPORT_ENGINEER
    assert request.employee_name == "Alice Morgan"


def test_onboarding_without_target_role_is_rejected():
    with pytest.raises(
        ValidationError,
        match="target_role is required for onboarding and role changes",
    ):
        AccessRequestCreate(
            event_id="evt-002",
            employee_id="EMP-1043",
            employee_name="Daniel Reed",
            department="support",
            action="onboard",
            requested_by="manager@example.test",
            reason="New employee starting on Tuesday",
        )


def test_offboarding_with_target_role_is_rejected():
    with pytest.raises(
        ValidationError,
        match="target_role must not be provided for offboarding",
    ):
        AccessRequestCreate(
            event_id="evt-003",
            employee_id="EMP-1044",
            employee_name="Morgan Lee",
            department="operations",
            action="offboard",
            target_role="operations_manager",
            requested_by="manager@example.test",
            reason="Employee is leaving the organization",
        )
