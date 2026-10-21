from contextlib import asynccontextmanager
import secrets
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db, init_database
from app.policies import RolePolicy
from app.policy_engine import get_role_policy
from app.responses import AccessRequestAccepted, AccessRequestDetail, AuditEventView
from app.schemas import AccessRequestCreate, ApprovalDecisionCreate, EmployeeRole
from app.services import (
    InvalidStateTransitionError,
    RequestNotFoundError,
    create_access_request as create_access_request_service,
    decide_access_request,
    get_access_request,
    list_audit_events,
    list_pending_requests,
    to_accepted,
    to_audit_view,
    to_detail,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    yield


def verify_approval_key(
    approval_key: Annotated[
        str | None,
        Header(alias="X-AccessFlow-Approval-Key"),
    ] = None,
) -> None:
    expected = get_settings().approval_api_key
    if approval_key is None or not secrets.compare_digest(
        approval_key,
        expected,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid approval credential",
        )


app = FastAPI(
    title="AccessFlow API",
    version="1.0.0",
    description=(
        "Human-approved, policy-driven SaaS access orchestration with "
        "idempotency and audit history."
    ),
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post(
    "/access-requests",
    response_model=AccessRequestAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_access_request(
    request: AccessRequestCreate,
    response: Response,
    session: Session = Depends(get_db),
) -> AccessRequestAccepted:
    record, duplicate = create_access_request_service(session, request)
    if duplicate:
        response.status_code = status.HTTP_200_OK
    return to_accepted(record, duplicate)


@app.get(
    "/access-requests/pending",
    response_model=list[AccessRequestDetail],
)
def read_pending_requests(
    session: Session = Depends(get_db),
) -> list[AccessRequestDetail]:
    return [to_detail(record) for record in list_pending_requests(session)]


@app.get(
    "/access-requests/{request_id}",
    response_model=AccessRequestDetail,
)
def read_access_request(
    request_id: UUID,
    session: Session = Depends(get_db),
) -> AccessRequestDetail:
    try:
        return to_detail(get_access_request(session, request_id))
    except RequestNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post(
    "/access-requests/{request_id}/decision",
    response_model=AccessRequestDetail,
)
def submit_approval_decision(
    request_id: UUID,
    decision: ApprovalDecisionCreate,
    _: None = Depends(verify_approval_key),
    session: Session = Depends(get_db),
) -> AccessRequestDetail:
    try:
        return to_detail(decide_access_request(session, request_id, decision))
    except RequestNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidStateTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.get(
    "/access-requests/{request_id}/audit",
    response_model=list[AuditEventView],
)
def read_audit_history(
    request_id: UUID,
    session: Session = Depends(get_db),
) -> list[AuditEventView]:
    try:
        return [
            to_audit_view(event)
            for event in list_audit_events(session, request_id)
        ]
    except RequestNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get(
    "/policies/{role}",
    response_model=RolePolicy,
)
def read_role_policy(role: EmployeeRole) -> RolePolicy:
    return get_role_policy(role)
