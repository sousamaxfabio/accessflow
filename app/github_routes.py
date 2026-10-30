from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.github_client import GitHubDirectoryClient
from app.github_dependencies import get_github_client
from app.github_errors import (
    GitHubAPIError,
    GitHubRateLimitError,
    GitHubResponseError,
    GitHubTimeoutError,
    GitHubUnavailableError,
)
from app.github_models import GitHubMembersResult

router = APIRouter(
    prefix="/integrations/github",
    tags=["integrations"],
)

OrganizationName = Annotated[
    str,
    Path(
        min_length=1,
        max_length=39,
        pattern=r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$",
    ),
]

GitHubClientDependency = Annotated[
    GitHubDirectoryClient,
    Depends(get_github_client),
]


@router.get(
    "/organizations/{organization}/members",
    response_model=GitHubMembersResult,
)
async def read_github_organization_members(
    organization: OrganizationName,
    client: GitHubClientDependency,
) -> GitHubMembersResult:
    try:
        return await client.list_organization_members(organization)
    except GitHubRateLimitError as error:
        headers = None
        if error.retry_after_seconds is not None:
            headers = {"Retry-After": str(max(1, ceil(error.retry_after_seconds)))}

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="GitHub API rate limit exceeded",
            headers=headers,
        ) from error
    except GitHubTimeoutError as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="GitHub API request timed out",
        ) from error
    except GitHubUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub API is temporarily unavailable",
        ) from error
    except GitHubAPIError as error:
        if error.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GitHub organization not found",
            ) from error

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub API rejected the request",
        ) from error
    except GitHubResponseError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub API returned an invalid response",
        ) from error
