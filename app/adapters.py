from typing import Protocol

from pydantic import BaseModel, ConfigDict

from app.policies import AccessGrant, ApplicationName
from app.schemas import AccessAction


class AdapterResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    application: ApplicationName
    operation: str
    status: str
    detail: str


class SaaSAdapter(Protocol):
    application: ApplicationName

    def apply(
        self,
        employee_id: str,
        action: AccessAction,
        grant: AccessGrant,
    ) -> AdapterResult: ...


class SimulatedSaaSAdapter:
    def __init__(self, application: ApplicationName) -> None:
        self.application = application

    def apply(
        self,
        employee_id: str,
        action: AccessAction,
        grant: AccessGrant,
    ) -> AdapterResult:
        operation = "revoke" if action == AccessAction.OFFBOARD else "grant"
        return AdapterResult(
            application=self.application,
            operation=operation,
            status="success",
            detail=(
                f"Simulated {operation} of {grant.permission} on "
                f"{grant.resource} for {employee_id}"
            ),
        )


ADAPTERS: dict[ApplicationName, SaaSAdapter] = {
    application: SimulatedSaaSAdapter(application)
    for application in ApplicationName
}


def execute_access_changes(
    employee_id: str,
    action: AccessAction,
    grants: tuple[AccessGrant, ...],
) -> tuple[AdapterResult, ...]:
    return tuple(
        ADAPTERS[grant.application].apply(employee_id, action, grant)
        for grant in grants
    )


def build_offboarding_grants() -> tuple[AccessGrant, ...]:
    return tuple(
        AccessGrant(
            application=application,
            permission="all_access",
            resource="employee_account",
        )
        for application in ApplicationName
    )
