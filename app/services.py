from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters import build_offboarding_grants, execute_access_changes
from app.models import AccessRequestRecord, AuditEventRecord
from app.policies import AccessGrant
from app.policy_engine import get_role_policy
from app.responses import (
    AccessRequestAccepted,
    AccessRequestDetail,
    AccessRequestStatus,
    AuditEventView,
)
from app.schemas import (
    AccessAction,
    AccessRequestCreate,
    ApprovalDecision,
    ApprovalDecisionCreate,
)


class RequestNotFoundError(LookupError):
    pass


class InvalidStateTransitionError(ValueError):
    pass


def _add_audit(
    session: Session,
    request_id: str,
    event_type: str,
    details: dict | None = None,
) -> None:
    session.add(
        AuditEventRecord(
            request_id=request_id,
            event_type=event_type,
            details=details or {},
        )
    )


def _grants_for(request: AccessRequestCreate) -> tuple[AccessGrant, ...]:
    if request.action == AccessAction.OFFBOARD:
        return build_offboarding_grants()
    assert request.target_role is not None
    return get_role_policy(request.target_role).grants


def _requires_approval(request: AccessRequestCreate) -> bool:
    if request.action == AccessAction.OFFBOARD:
        return False
    assert request.target_role is not None
    return get_role_policy(request.target_role).requires_approval


def _execute(record: AccessRequestRecord) -> None:
    grants = tuple(
        AccessGrant.model_validate(grant) for grant in record.policy_snapshot
    )
    record.status = AccessRequestStatus.EXECUTING.value
    results = execute_access_changes(
        record.employee_id,
        AccessAction(record.action),
        grants,
    )
    record.execution_results = [
        result.model_dump(mode="json") for result in results
    ]
    record.status = AccessRequestStatus.COMPLETED.value


def create_access_request(
    session: Session,
    request: AccessRequestCreate,
) -> tuple[AccessRequestRecord, bool]:
    existing = session.scalar(
        select(AccessRequestRecord).where(
            AccessRequestRecord.event_id == request.event_id
        )
    )
    if existing is not None:
        return existing, True

    grants = _grants_for(request)
    requires_approval = _requires_approval(request)
    request_id = str(uuid4())
    record = AccessRequestRecord(
        id=request_id,
        event_id=request.event_id,
        employee_id=request.employee_id,
        employee_name=request.employee_name,
        department=request.department.value,
        action=request.action.value,
        target_role=(request.target_role.value if request.target_role else None),
        requested_by=request.requested_by,
        reason=request.reason,
        status=(
            AccessRequestStatus.PENDING_APPROVAL.value
            if requires_approval
            else AccessRequestStatus.SUBMITTED.value
        ),
        requires_approval=requires_approval,
        policy_snapshot=[grant.model_dump(mode="json") for grant in grants],
    )
    session.add(record)
    _add_audit(
        session,
        request_id,
        "request_submitted",
        {"event_id": request.event_id, "action": request.action.value},
    )
    _add_audit(
        session,
        request_id,
        "policy_evaluated",
        {
            "target_role": record.target_role,
            "requires_approval": requires_approval,
            "grant_count": len(grants),
        },
    )

    if requires_approval:
        _add_audit(session, request_id, "approval_requested")
    else:
        _execute(record)
        _add_audit(
            session,
            request_id,
            "provisioning_completed",
            {"result_count": len(record.execution_results)},
        )

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.scalar(
            select(AccessRequestRecord).where(
                AccessRequestRecord.event_id == request.event_id
            )
        )
        if existing is None:
            raise
        return existing, True
    session.refresh(record)
    return record, False


def get_access_request(
    session: Session,
    request_id: UUID | str,
) -> AccessRequestRecord:
    record = session.get(AccessRequestRecord, str(request_id))
    if record is None:
        raise RequestNotFoundError(f"Access request not found: {request_id}")
    return record


def decide_access_request(
    session: Session,
    request_id: UUID | str,
    decision: ApprovalDecisionCreate,
) -> AccessRequestRecord:
    record = get_access_request(session, request_id)
    if record.status != AccessRequestStatus.PENDING_APPROVAL.value:
        raise InvalidStateTransitionError(
            f"Request {request_id} is not pending approval"
        )

    record.approval_decision = decision.decision.value
    record.approval_reviewer = decision.reviewer
    record.approval_comments = decision.comments
    _add_audit(
        session,
        record.id,
        "approval_decided",
        {
            "decision": decision.decision.value,
            "reviewer": decision.reviewer,
            "comments": decision.comments,
        },
    )

    if decision.decision == ApprovalDecision.REJECT:
        record.status = AccessRequestStatus.REJECTED.value
    else:
        record.status = AccessRequestStatus.APPROVED.value
        _execute(record)
        _add_audit(
            session,
            record.id,
            "provisioning_completed",
            {"result_count": len(record.execution_results)},
        )

    session.commit()
    session.refresh(record)
    return record


def list_pending_requests(session: Session) -> list[AccessRequestRecord]:
    return list(
        session.scalars(
            select(AccessRequestRecord)
            .where(
                AccessRequestRecord.status
                == AccessRequestStatus.PENDING_APPROVAL.value
            )
            .order_by(AccessRequestRecord.created_at)
        )
    )


def list_audit_events(
    session: Session,
    request_id: UUID | str,
) -> list[AuditEventRecord]:
    get_access_request(session, request_id)
    return list(
        session.scalars(
            select(AuditEventRecord)
            .where(AuditEventRecord.request_id == str(request_id))
            .order_by(AuditEventRecord.id)
        )
    )


def to_accepted(
    record: AccessRequestRecord,
    duplicate: bool = False,
) -> AccessRequestAccepted:
    return AccessRequestAccepted(
        request_id=UUID(record.id),
        event_id=record.event_id,
        status=AccessRequestStatus(record.status),
        requires_approval=record.requires_approval,
        duplicate=duplicate,
    )


def to_detail(
    record: AccessRequestRecord,
    duplicate: bool = False,
) -> AccessRequestDetail:
    return AccessRequestDetail(
        **to_accepted(record, duplicate).model_dump(),
        employee_id=record.employee_id,
        employee_name=record.employee_name,
        department=record.department,
        action=record.action,
        target_role=record.target_role,
        requested_by=record.requested_by,
        reason=record.reason,
        policy=[AccessGrant.model_validate(item) for item in record.policy_snapshot],
        execution_results=record.execution_results,
        approval_decision=record.approval_decision,
        approval_reviewer=record.approval_reviewer,
        approval_comments=record.approval_comments,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def to_audit_view(event: AuditEventRecord) -> AuditEventView:
    return AuditEventView(
        id=event.id,
        request_id=UUID(event.request_id),
        event_type=event.event_type,
        details=event.details,
        created_at=event.created_at,
    )
