from app.policies import ROLE_POLICIES
from app.schemas import EmployeeRole


def test_every_employee_role_has_an_explicit_policy():
    assert set(ROLE_POLICIES) == set(EmployeeRole)


def test_policy_key_matches_the_embedded_role():
    for role, policy in ROLE_POLICIES.items():
        assert policy.role == role
