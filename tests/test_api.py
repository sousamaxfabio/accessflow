from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

APPROVAL_HEADERS = {"X-AccessFlow-Approval-Key": "local-development-only"}


@pytest.fixture
def client() -> Generator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    Base.metadata.create_all(engine)

    def override_get_db() -> Generator[Session]:
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def onboarding_payload(
    event_id: str,
    target_role: str = "support_engineer",
) -> dict[str, str]:
    return {
        "event_id": event_id,
        "employee_id": "EMP-2001",
        "employee_name": "Alice Morgan",
        "department": "support",
        "action": "onboard",
        "target_role": target_role,
        "requested_by": "manager@example.test",
        "reason": "New employee starting on Monday",
    }


def test_non_sensitive_request_completes_automatically(client: TestClient):
    response = client.post(
        "/access-requests",
        json=onboarding_payload("api-auto-001"),
    )

    assert response.status_code == 202
    accepted = response.json()
    assert accepted["status"] == "completed"
    assert accepted["requires_approval"] is False
    assert accepted["duplicate"] is False

    detail = client.get(f"/access-requests/{accepted['request_id']}").json()
    assert len(detail["policy"]) == 3
    assert len(detail["execution_results"]) == 3
    assert all(result["status"] == "success" for result in detail["execution_results"])


def test_duplicate_event_returns_original_request(client: TestClient):
    payload = onboarding_payload("api-duplicate-001")
    first = client.post("/access-requests", json=payload)
    second = client.post("/access-requests", json=payload)

    assert first.status_code == 202
    assert second.status_code == 200
    assert second.json()["duplicate"] is True
    assert second.json()["request_id"] == first.json()["request_id"]


def test_sensitive_request_waits_for_approval_then_completes(
    client: TestClient,
):
    response = client.post(
        "/access-requests",
        json=onboarding_payload(
            "api-approval-001",
            target_role="automation_engineer",
        ),
    )
    accepted = response.json()

    assert accepted["status"] == "pending_approval"
    assert accepted["requires_approval"] is True

    pending = client.get("/access-requests/pending").json()
    assert [item["request_id"] for item in pending] == [accepted["request_id"]]

    decision = client.post(
        f"/access-requests/{accepted['request_id']}/decision",
        headers=APPROVAL_HEADERS,
        json={
            "decision": "approve",
            "reviewer": "IT Reviewer",
            "comments": "Business justification confirmed",
        },
    )

    assert decision.status_code == 200
    completed = decision.json()
    assert completed["status"] == "completed"
    assert completed["approval_decision"] == "approve"
    assert len(completed["execution_results"]) == 4

    audit = client.get(f"/access-requests/{accepted['request_id']}/audit").json()
    assert [event["event_type"] for event in audit] == [
        "request_submitted",
        "policy_evaluated",
        "approval_requested",
        "approval_decided",
        "provisioning_completed",
    ]


def test_rejected_request_cannot_be_decided_twice(client: TestClient):
    accepted = client.post(
        "/access-requests",
        json=onboarding_payload(
            "api-reject-001",
            target_role="finance_analyst",
        ),
    ).json()
    decision_body = {
        "decision": "reject",
        "reviewer": "Security Reviewer",
        "comments": "Requested role does not match the approved position",
    }

    rejected = client.post(
        f"/access-requests/{accepted['request_id']}/decision",
        headers=APPROVAL_HEADERS,
        json=decision_body,
    )
    repeated = client.post(
        f"/access-requests/{accepted['request_id']}/decision",
        headers=APPROVAL_HEADERS,
        json=decision_body,
    )

    assert rejected.json()["status"] == "rejected"
    assert rejected.json()["execution_results"] == []
    assert repeated.status_code == 409


def test_approval_decision_requires_authentication(client: TestClient):
    accepted = client.post(
        "/access-requests",
        json=onboarding_payload(
            "api-auth-001",
            target_role="automation_engineer",
        ),
    ).json()

    response = client.post(
        f"/access-requests/{accepted['request_id']}/decision",
        json={
            "decision": "approve",
            "reviewer": "Untrusted caller",
            "comments": "Attempt without the approval credential",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid approval credential"


def test_offboarding_revokes_all_simulated_services(client: TestClient):
    payload = onboarding_payload("api-offboard-001")
    payload.update(
        {
            "action": "offboard",
            "target_role": None,
            "reason": "Employee has left the organization",
        }
    )

    response = client.post("/access-requests", json=payload)
    detail = client.get(f"/access-requests/{response.json()['request_id']}").json()

    assert response.json()["status"] == "completed"
    assert len(detail["execution_results"]) == 4
    assert {result["operation"] for result in detail["execution_results"]} == {"revoke"}


def test_unknown_role_is_rejected_before_policy_evaluation(client: TestClient):
    response = client.post(
        "/access-requests",
        json=onboarding_payload(
            "api-unknown-001",
            target_role="marketing_manager",
        ),
    )

    assert response.status_code == 422


def test_policy_endpoint_is_read_only_and_explains_access(client: TestClient):
    response = client.get("/policies/automation_engineer")

    assert response.status_code == 200
    policy = response.json()
    assert policy["role"] == "automation_engineer"
    assert policy["requires_approval"] is True
    assert any(
        grant["application"] == "github" and grant["permission"] == "write"
        for grant in policy["grants"]
    )


def test_openapi_schema_documents_the_complete_api(client: TestClient):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/access-requests" in paths
    assert "/access-requests/{request_id}/decision" in paths
    assert "/access-requests/{request_id}/audit" in paths
    assert "/policies/{role}" in paths
