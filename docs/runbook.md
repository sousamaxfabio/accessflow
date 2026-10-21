# Operations runbook

## Local Python mode

1. Create and activate `.venv`.
2. Install `requirements.txt`.
3. Run `python -m alembic upgrade head`.
4. Run `python -m uvicorn app.main:app --reload`.
5. Open `http://127.0.0.1:8000/docs`.

SQLite is used when `ACCESSFLOW_DATABASE_URL` is not set.

## Docker and PostgreSQL mode

Run `docker compose up --build`. The API becomes available on port 8000 after
PostgreSQL is healthy and the migration completes.

## MCP mode

Run `python mcp_server.py` for stdio, or use `mcp dev mcp_server.py` to inspect
the server. The MCP process uses the same `ACCESSFLOW_DATABASE_URL` as the API.

## Troubleshooting

### `No module named pytest`

The virtual environment is not active. In PowerShell, temporarily allow the
activation script for the current process, then activate `.venv`.

### Database connection refused

Confirm the PostgreSQL container is healthy and that the hostname is `db` from
inside Compose. From Windows outside Compose, use `localhost` and an exposed
database port instead.

### Request remains pending

This is expected for sensitive grants. Submit an approval decision using the
request ID or the approval-decision n8n workflow.

### Duplicate response

The same `event_id` was already processed. Use a new event ID only for a truly
new business event; do not bypass idempotency to retry provisioning.
