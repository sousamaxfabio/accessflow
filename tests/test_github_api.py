from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.github_dependencies import get_github_client
from app.github_errors import (
    GitHubAPIError,
    GitHubRateLimitError,
    GitHubResponseError,
    GitHubTimeoutError,
    GitHubUnavailableError,
)
from app.github_models import GitHubMember, GitHubMembersResult
from app.main import app


class FakeGitHubClient:
    def __init__(self) -> None:
        self.error: Exception | None = None
        self.result = GitHubMembersResult(
            organization="example-org",
            members=[
                GitHubMember(
                    login="alice",
                    id=101,
                    avatar_url="https://avatars.example.test/alice",
                    html_url="https://github.example.test/alice",
                )
            ],
            pages_fetched=1,
            truncated=False,
        )

    async def list_organization_members(
        self,
        organization: str,
    ) -> GitHubMembersResult:
        if self.error is not None:
            raise self.error

        return self.result.model_copy(update={"organization": organization})


@pytest.fixture
def api_client() -> Generator[tuple[TestClient, FakeGitHubClient]]:
    fake_client = FakeGitHubClient()
    app.dependency_overrides[get_github_client] = lambda: fake_client

    with TestClient(app) as client:
        yield client, fake_client

    app.dependency_overrides.pop(get_github_client, None)


def test_github_endpoint_returns_validated_members(
    api_client: tuple[TestClient, FakeGitHubClient],
):
    client, _ = api_client

    response = client.get("/integrations/github/organizations/example-org/members")

    assert response.status_code == 200
    assert response.json() == {
        "organization": "example-org",
        "members": [
            {
                "login": "alice",
                "id": 101,
                "avatar_url": "https://avatars.example.test/alice",
                "html_url": "https://github.example.test/alice",
            }
        ],
        "pages_fetched": 1,
        "truncated": False,
    }


def test_github_endpoint_rejects_invalid_organization_name(
    api_client: tuple[TestClient, FakeGitHubClient],
):
    client, _ = api_client

    response = client.get("/integrations/github/organizations/-invalid-/members")

    assert response.status_code == 422


def test_github_rate_limit_returns_retry_after_header(
    api_client: tuple[TestClient, FakeGitHubClient],
):
    client, fake_client = api_client
    fake_client.error = GitHubRateLimitError(3.2)

    response = client.get("/integrations/github/organizations/example-org/members")

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "4"
    assert response.json()["detail"] == "GitHub API rate limit exceeded"


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (GitHubTimeoutError(), 504),
        (GitHubUnavailableError(), 503),
        (GitHubAPIError(404, "Not found"), 404),
        (GitHubAPIError(401, "Bad credentials"), 502),
        (GitHubResponseError(), 502),
    ],
)
def test_github_failures_are_translated_to_http_responses(
    api_client: tuple[TestClient, FakeGitHubClient],
    error: Exception,
    expected_status: int,
):
    client, fake_client = api_client
    fake_client.error = error

    response = client.get("/integrations/github/organizations/example-org/members")

    assert response.status_code == expected_status
