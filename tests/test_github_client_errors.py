import httpx
import pytest

from app.github_client import GitHubDirectoryClient
from app.github_errors import (
    GitHubAPIError,
    GitHubRateLimitError,
    GitHubResponseError,
    GitHubTimeoutError,
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def valid_member() -> dict[str, object]:
    return {
        "login": "alice",
        "id": 101,
        "avatar_url": "https://avatars.example.test/alice",
        "html_url": "https://github.example.test/alice",
    }


@pytest.mark.anyio
async def test_retries_temporary_server_error_then_succeeds():
    attempts = 0
    delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            return httpx.Response(
                503,
                json={"message": "Service unavailable"},
            )

        return httpx.Response(
            200,
            json=[valid_member()],
        )

    async with httpx.AsyncClient(
        base_url="https://api.github.test",
        transport=httpx.MockTransport(handler),
    ) as http_client:
        client = GitHubDirectoryClient(
            http_client=http_client,
            max_retries=2,
            retry_base_seconds=0.5,
            max_pages=1,
            sleep=fake_sleep,
        )

        result = await client.list_organization_members("example-org")

    assert attempts == 2
    assert delays == [0.5]
    assert result.members[0].login == "alice"


@pytest.mark.anyio
async def test_timeout_retries_then_raises_specific_error():
    attempts = 0
    delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout(
            "Simulated timeout",
            request=request,
        )

    async with httpx.AsyncClient(
        base_url="https://api.github.test",
        transport=httpx.MockTransport(handler),
    ) as http_client:
        client = GitHubDirectoryClient(
            http_client=http_client,
            max_retries=2,
            retry_base_seconds=0.25,
            max_pages=1,
            sleep=fake_sleep,
        )

        with pytest.raises(GitHubTimeoutError):
            await client.list_organization_members("example-org")

    assert attempts == 3
    assert delays == [0.25, 0.5]


@pytest.mark.anyio
async def test_rate_limit_exposes_retry_timing_without_retrying():
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            429,
            json={"message": "API rate limit exceeded"},
            headers={"Retry-After": "3.5"},
        )

    async with httpx.AsyncClient(
        base_url="https://api.github.test",
        transport=httpx.MockTransport(handler),
    ) as http_client:
        client = GitHubDirectoryClient(
            http_client=http_client,
            max_retries=2,
            retry_base_seconds=0,
            max_pages=1,
        )

        with pytest.raises(GitHubRateLimitError) as error_info:
            await client.list_organization_members("example-org")

    assert attempts == 1
    assert error_info.value.retry_after_seconds == 3.5


@pytest.mark.anyio
async def test_non_retryable_error_preserves_status_and_detail():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={"message": "Organization not found"},
        )

    async with httpx.AsyncClient(
        base_url="https://api.github.test",
        transport=httpx.MockTransport(handler),
    ) as http_client:
        client = GitHubDirectoryClient(
            http_client=http_client,
            max_retries=2,
            retry_base_seconds=0,
            max_pages=1,
        )

        with pytest.raises(GitHubAPIError) as error_info:
            await client.list_organization_members("missing-org")

    assert error_info.value.status_code == 404
    assert error_info.value.detail == "Organization not found"


@pytest.mark.anyio
async def test_invalid_response_contract_is_rejected():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[{"login": "missing-required-fields"}],
        )

    async with httpx.AsyncClient(
        base_url="https://api.github.test",
        transport=httpx.MockTransport(handler),
    ) as http_client:
        client = GitHubDirectoryClient(
            http_client=http_client,
            max_retries=2,
            retry_base_seconds=0,
            max_pages=1,
        )

        with pytest.raises(GitHubResponseError):
            await client.list_organization_members("example-org")
