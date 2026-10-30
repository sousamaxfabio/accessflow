from app.config import Settings
from app.github_dependencies import build_github_headers


def test_github_headers_support_public_requests_without_token():
    settings = Settings(
        _env_file=None,
        github_token=None,
    )

    headers = build_github_headers(settings)

    assert headers == {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
        "User-Agent": "AccessFlow/1.0",
    }


def test_github_headers_add_bearer_authentication():
    settings = Settings(
        _env_file=None,
        github_token="test-github-token",
    )

    headers = build_github_headers(settings)

    assert headers["Authorization"] == "Bearer test-github-token"


def test_blank_github_token_is_not_sent():
    settings = Settings(
        _env_file=None,
        github_token="   ",
    )

    headers = build_github_headers(settings)

    assert "Authorization" not in headers
