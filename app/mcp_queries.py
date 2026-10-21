from uuid import UUID

from sqlalchemy.orm import Session

from app.policy_engine import get_role_policy
from app.schemas import EmployeeRole
from app.services import (
    get_access_request,
    list_pending_requests,
    to_detail,
)


def explain_role_access_data(role: str) -> dict:
    try:
        employee_role = EmployeeRole(role)
    except ValueError as error:
        allowed = ", ".join(item.value for item in EmployeeRole)
        raise ValueError(
            f"Unknown role '{role}'. Allowed roles: {allowed}"
        ) from error
    return get_role_policy(employee_role).model_dump(mode="json")


def get_access_request_data(session: Session, request_id: str) -> dict:
    parsed_id = UUID(request_id)
    return to_detail(
        get_access_request(session, parsed_id)
    ).model_dump(mode="json")


def list_pending_approval_data(
    session: Session,
    limit: int = 25,
) -> list[dict]:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    return [
        to_detail(record).model_dump(mode="json")
        for record in list_pending_requests(session)[:limit]
    ]
