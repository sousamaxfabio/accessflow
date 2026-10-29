"""Create access request and audit tables.

Revision ID: 20261021_0001
Revises:
Create Date: 2026-10-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261021_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "access_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=100), nullable=False),
        sa.Column("employee_id", sa.String(length=50), nullable=False),
        sa.Column("employee_name", sa.String(length=100), nullable=False),
        sa.Column("department", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("target_role", sa.String(length=50), nullable=True),
        sa.Column("requested_by", sa.String(length=100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("requires_approval", sa.Boolean(), nullable=False),
        sa.Column("policy_snapshot", sa.JSON(), nullable=False),
        sa.Column("execution_results", sa.JSON(), nullable=False),
        sa.Column("approval_decision", sa.String(length=20), nullable=True),
        sa.Column("approval_reviewer", sa.String(length=100), nullable=True),
        sa.Column("approval_comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_access_requests_employee_id",
        "access_requests",
        ["employee_id"],
    )
    op.create_index(
        "ix_access_requests_event_id",
        "access_requests",
        ["event_id"],
        unique=True,
    )
    op.create_index(
        "ix_access_requests_status",
        "access_requests",
        ["status"],
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["access_requests.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_events_event_type",
        "audit_events",
        ["event_type"],
    )
    op.create_index(
        "ix_audit_events_request_id",
        "audit_events",
        ["request_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_events_request_id", table_name="audit_events")
    op.drop_index("ix_audit_events_event_type", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_access_requests_status", table_name="access_requests")
    op.drop_index("ix_access_requests_event_id", table_name="access_requests")
    op.drop_index("ix_access_requests_employee_id", table_name="access_requests")
    op.drop_table("access_requests")
