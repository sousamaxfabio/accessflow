class GitHubIntegrationError(Exception):
    """Base class for failures while communicating with GitHub."""


class GitHubTimeoutError(GitHubIntegrationError):
    """GitHub did not respond before the configured timeout."""


class GitHubUnavailableError(GitHubIntegrationError):
    """GitHub remained unavailable after retry attempts."""


class GitHubRateLimitError(GitHubIntegrationError):
    """GitHub rejected the request because its rate limit was reached."""

    def __init__(self, retry_after_seconds: float | None) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__("GitHub API rate limit exceeded")


class GitHubAPIError(GitHubIntegrationError):
    """GitHub returned a non-retryable HTTP error."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"GitHub API returned {status_code}: {detail}")


class GitHubResponseError(GitHubIntegrationError):
    """GitHub returned data that did not match the expected contract."""
