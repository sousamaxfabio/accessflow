import asyncio
from collections.abc import Awaitable, Callable
from time import time

import httpx
from pydantic import ValidationError

from app.github_errors import (
    GitHubAPIError,
    GitHubRateLimitError,
    GitHubResponseError,
    GitHubTimeoutError,
    GitHubUnavailableError,
)
from app.github_models import GitHubMember, GitHubMembersResult

SleepFunction = Callable[[float], Awaitable[None]]
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}


class GitHubDirectoryClient:
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        max_retries: int,
        retry_base_seconds: float,
        max_pages: int,
        sleep: SleepFunction = asyncio.sleep,
    ) -> None:
        self.http_client = http_client
        self.max_retries = max_retries
        self.retry_base_seconds = retry_base_seconds
        self.max_pages = max_pages
        self.sleep = sleep

    async def list_organization_members(
        self,
        organization: str,
    ) -> GitHubMembersResult:
        members: list[GitHubMember] = []

        for page in range(1, self.max_pages + 1):
            response = await self._request_page(
                organization=organization,
                page=page,
            )
            members.extend(self._parse_members(response))

            if "next" not in response.links:
                return GitHubMembersResult(
                    organization=organization,
                    members=members,
                    pages_fetched=page,
                    truncated=False,
                )

        return GitHubMembersResult(
            organization=organization,
            members=members,
            pages_fetched=self.max_pages,
            truncated=True,
        )

    async def _request_page(
        self,
        organization: str,
        page: int,
    ) -> httpx.Response:
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.http_client.get(
                    f"/orgs/{organization}/members",
                    params={
                        "per_page": 100,
                        "page": page,
                    },
                )
            except httpx.TimeoutException as error:
                if attempt == self.max_retries:
                    raise GitHubTimeoutError("GitHub API request timed out") from error

                await self._wait_before_retry(attempt)
                continue
            except httpx.RequestError as error:
                if attempt == self.max_retries:
                    raise GitHubUnavailableError(
                        "GitHub API network request failed"
                    ) from error

                await self._wait_before_retry(attempt)
                continue

            if self._is_rate_limited(response):
                raise GitHubRateLimitError(self._get_retry_after_seconds(response))

            if response.status_code in RETRYABLE_STATUS_CODES:
                if attempt == self.max_retries:
                    raise GitHubUnavailableError(
                        "GitHub API remained unavailable after retries"
                    )

                await self._wait_before_retry(attempt)
                continue

            if response.is_error:
                raise GitHubAPIError(
                    status_code=response.status_code,
                    detail=self._get_error_detail(response),
                )

            return response

        raise GitHubUnavailableError("GitHub API request ended without a response")

    async def _wait_before_retry(self, attempt: int) -> None:
        delay = self.retry_base_seconds * (2**attempt)
        if delay > 0:
            await self.sleep(delay)

    @staticmethod
    def _parse_members(response: httpx.Response) -> list[GitHubMember]:
        try:
            payload = response.json()
        except ValueError as error:
            raise GitHubResponseError("GitHub returned invalid JSON") from error

        if not isinstance(payload, list):
            raise GitHubResponseError("GitHub member response must be a list")

        try:
            return [GitHubMember.model_validate(member) for member in payload]
        except ValidationError as error:
            raise GitHubResponseError(
                "GitHub member response failed validation"
            ) from error

    @classmethod
    def _is_rate_limited(cls, response: httpx.Response) -> bool:
        if response.status_code == 429:
            return True

        if response.status_code != 403:
            return False

        remaining = response.headers.get("x-ratelimit-remaining")
        detail = cls._get_error_detail(response).lower()

        return remaining == "0" or "rate limit" in detail

    @staticmethod
    def _get_retry_after_seconds(
        response: httpx.Response,
    ) -> float | None:
        retry_after = response.headers.get("retry-after")
        if retry_after is not None:
            try:
                return max(float(retry_after), 0)
            except ValueError:
                return None

        reset_at = response.headers.get("x-ratelimit-reset")
        if reset_at is not None:
            try:
                return max(float(reset_at) - time(), 0)
            except ValueError:
                return None

        return None

    @staticmethod
    def _get_error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text or response.reason_phrase

        if isinstance(payload, dict):
            message = payload.get("message")
            if isinstance(message, str):
                return message

        return response.text or response.reason_phrase
