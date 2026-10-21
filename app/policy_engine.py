from app.policies import ROLE_POLICIES, RolePolicy
from app.schemas import EmployeeRole


class PolicyNotFoundError(ValueError):
    """Raised when no explicit access policy exists for a role."""


def get_role_policy(role: EmployeeRole) -> RolePolicy:
    try:
        return ROLE_POLICIES[role]
    except KeyError as error:
        raise PolicyNotFoundError(
            f"No access policy is defined for role: {role.value}"
        ) from error