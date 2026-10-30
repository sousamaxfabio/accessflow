# GitHub directory integration

AccessFlow provides a read-only integration with GitHub's REST API for listing
organization members.

The integration does not create accounts, change permissions, invite users, or
modify GitHub resources.

## Endpoint

```text
GET /integrations/github/organizations/{organization}/members
```

Organization names must:

- contain between 1 and 39 characters;
- contain only letters, numbers, and hyphens;
- not begin or end with a hyphen.

## Example response

```json
{
  "organization": "octokit",
  "members": [
    {
      "login": "example-user",
      "id": 101,
      "avatar_url": "https://avatars.githubusercontent.com/u/101",
      "html_url": "https://github.com/example-user"
    }
  ],
  "pages_fetched": 1,
  "truncated": false
}
```

`truncated` is `true` when GitHub reports another page but AccessFlow reaches
its configured page limit.

## Configuration

| Variable | Default | Purpose |
|---|---:|---|
| `ACCESSFLOW_GITHUB_API_URL` | `https://api.github.com` | GitHub REST API base URL |
| `ACCESSFLOW_GITHUB_API_VERSION` | `2026-03-10` | GitHub API contract version |
| `ACCESSFLOW_GITHUB_TOKEN` | unset | Optional read-only bearer token |
| `ACCESSFLOW_GITHUB_TIMEOUT_SECONDS` | `5` | Timeout for each GitHub request |
| `ACCESSFLOW_GITHUB_MAX_RETRIES` | `2` | Retries after transient failures |
| `ACCESSFLOW_GITHUB_RETRY_BASE_SECONDS` | `0.25` | Initial exponential-backoff delay |
| `ACCESSFLOW_GITHUB_MAX_PAGES` | `5` | Maximum pages retrieved per request |

Public organization members can be requested without a token. A token can
provide a higher rate limit and access appropriate to that token's permissions.
Never commit a real token.

## Retry behaviour

AccessFlow retries:

- network failures;
- timeouts;
- HTTP `500`, `502`, `503`, and `504` responses.

The delay grows exponentially. With the default base delay, waits are:

```text
0.25 seconds, then 0.5 seconds
```

Rate-limit responses are not retried blindly. AccessFlow returns `429` and
forwards a calculated `Retry-After` header when GitHub supplies retry timing.

## Error translation

| GitHub/client failure | AccessFlow response |
|---|---:|
| Rate limit | `429 Too Many Requests` |
| Timeout after retries | `504 Gateway Timeout` |
| Network/server failure after retries | `503 Service Unavailable` |
| Organization not found | `404 Not Found` |
| Other GitHub HTTP error | `502 Bad Gateway` |
| Invalid GitHub response data | `502 Bad Gateway` |

## Pagination

AccessFlow requests up to 100 members per page. It follows GitHub's `Link`
header while a `next` relation exists and stops at
`ACCESSFLOW_GITHUB_MAX_PAGES`.

Requests are sequential to reduce pressure on GitHub's secondary rate limits.

## Local verification

For local SQLite mode:

```powershell
$env:ACCESSFLOW_DATABASE_URL = "sqlite:///./accessflow-demo.db"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

From another terminal:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/integrations/github/organizations/octokit/members"
```

The integration uses a shared `httpx.AsyncClient`, created when FastAPI starts
and closed automatically when FastAPI stops. This preserves connection pooling
and avoids creating a new network client for every request.

## Testing

Automated tests use `httpx.MockTransport`; they do not call GitHub.

The suite covers:

- response validation;
- pagination and page limits;
- transient-server retries;
- timeout retries;
- exponential backoff;
- rate-limit handling;
- authentication headers;
- FastAPI error translation.
