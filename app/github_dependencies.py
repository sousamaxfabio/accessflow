from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import Request

from app.config import Settings
from app.github_client import GitHubDirectoryClient


def build_github_headers(settings: Settings) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": settings.github_api_version,
        "User-Agent": "AccessFlow/1.0",
    }

    if settings.github_token is not None:
        token = settings.github_token.get_secret_value().strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"

    return headers


@asynccontextmanager
async def github_client_context(
    settings: Settings,
) -> AsyncIterator[GitHubDirectoryClient]:
    async with httpx.AsyncClient(
        base_url=settings.github_api_url,
        headers=build_github_headers(settings),
        timeout=httpx.Timeout(settings.github_timeout_seconds),
    ) as http_client:
        yield GitHubDirectoryClient(
            http_client=http_client,
            max_retries=settings.github_max_retries,
            retry_base_seconds=settings.github_retry_base_seconds,
            max_pages=settings.github_max_pages,
        )


def get_github_client(request: Request) -> GitHubDirectoryClient:
    client = getattr(request.app.state, "github_client", None)
    if not isinstance(client, GitHubDirectoryClient):
        raise RuntimeError("GitHub client is not initialized")

    return client
