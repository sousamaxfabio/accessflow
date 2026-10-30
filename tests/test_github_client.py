import httpx
import pytest

from app.github_client import GitHubDirectoryClient


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def github_member(login: str, member_id: int) -> dict[str, object]:
    return {
        "login": login,
        "id": member_id,
        "avatar_url": f"https://avatars.example.test/{login}",
        "html_url": f"https://github.example.test/{login}",
        "unused_github_field": "ignored",
    }


@pytest.mark.anyio
async def test_lists_and_validates_one_page_of_members():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/orgs/example-org/members"
        assert request.url.params["per_page"] == "100"
        assert request.url.params["page"] == "1"

        return httpx.Response(
            200,
            json=[
                github_member("alice", 101),
                github_member("bob", 102),
            ],
        )

    async with httpx.AsyncClient(
        base_url="https://api.github.test",
        transport=httpx.MockTransport(handler),
    ) as http_client:
        client = GitHubDirectoryClient(
            http_client=http_client,
            max_retries=2,
            retry_base_seconds=0,
            max_pages=5,
        )

        result = await client.list_organization_members("example-org")

    assert [member.login for member in result.members] == [
        "alice",
        "bob",
    ]
    assert result.pages_fetched == 1
    assert result.truncated is False


@pytest.mark.anyio
async def test_follows_github_pagination():
    requested_pages: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = request.url.params["page"]
        requested_pages.append(page)

        if page == "1":
            return httpx.Response(
                200,
                json=[github_member("alice", 101)],
                headers={
                    "Link": (
                        "<https://api.github.test/orgs/example-org/"
                        'members?per_page=100&page=2>; rel="next"'
                    )
                },
            )

        return httpx.Response(
            200,
            json=[github_member("bob", 102)],
        )

    async with httpx.AsyncClient(
        base_url="https://api.github.test",
        transport=httpx.MockTransport(handler),
    ) as http_client:
        client = GitHubDirectoryClient(
            http_client=http_client,
            max_retries=2,
            retry_base_seconds=0,
            max_pages=5,
        )

        result = await client.list_organization_members("example-org")

    assert requested_pages == ["1", "2"]
    assert [member.login for member in result.members] == [
        "alice",
        "bob",
    ]
    assert result.pages_fetched == 2
    assert result.truncated is False


@pytest.mark.anyio
async def test_marks_results_truncated_at_page_limit():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[github_member("alice", 101)],
            headers={
                "Link": (
                    "<https://api.github.test/orgs/example-org/"
                    'members?per_page=100&page=2>; rel="next"'
                )
            },
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

        result = await client.list_organization_members("example-org")

    assert result.pages_fetched == 1
    assert result.truncated is True
