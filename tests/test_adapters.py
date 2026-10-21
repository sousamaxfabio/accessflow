from app.adapters import build_offboarding_grants, execute_access_changes
from app.policies import ApplicationName
from app.schemas import AccessAction


def test_offboarding_adapter_plan_covers_every_application():
    grants = build_offboarding_grants()
    results = execute_access_changes(
        "EMP-9999",
        AccessAction.OFFBOARD,
        grants,
    )

    assert {result.application for result in results} == set(ApplicationName)
    assert {result.operation for result in results} == {"revoke"}
    assert {result.status for result in results} == {"success"}
