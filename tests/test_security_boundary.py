import pytest
from pydantic import ValidationError

from app.schemas import AccessRequestCreate


def test_request_cannot_set_system_controlled_status():
    payload = {
        "event_id": "evt-004",
        "employee_id": "EMP-1045",
        "employee_name": "Jamie Stone",
        "department": "engineering",
        "action": "onboard",
        "target_role": "automation_engineer",
        "requested_by": "manager@example.test",
        "reason": "New engineer requires standard team access",
        "status": "approved",
    }

    with pytest.raises(
        ValidationError,
        match="Extra inputs are not permitted",
    ):
        AccessRequestCreate.model_validate(payload)
