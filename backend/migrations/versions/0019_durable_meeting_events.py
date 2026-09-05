"""Add durable meeting event history for realtime replay."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019_durable_meeting_events"
down_revision: str | None = "0018_team_invitations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "meeting_events",
        sa.Column("sequence", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("meeting_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("event_id", name="uq_meeting_events_event_id"),
    )
    op.create_index(
        "ix_meeting_events_meeting_sequence", "meeting_events", ["meeting_id", "sequence"]
    )
    op.create_index(
        "ix_meeting_events_meeting_recipient_sequence",
        "meeting_events",
        ["meeting_id", "recipient_user_id", "sequence"],
    )


def downgrade() -> None:
    op.drop_index("ix_meeting_events_meeting_recipient_sequence", table_name="meeting_events")
    op.drop_index("ix_meeting_events_meeting_sequence", table_name="meeting_events")
    op.drop_table("meeting_events")
