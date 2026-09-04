"""Create core user, team, and meeting tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_core_models"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

uuid_type = postgresql.UUID(as_uuid=True)
timestamp_type = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255)),
        sa.Column("email", sa.String(length=320)),
        sa.Column("created_at", timestamp_type, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("external_id", name="uq_users_external_id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "teams",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", timestamp_type, server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "team_members",
        sa.Column("team_id", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("role", sa.String(length=32), server_default="member", nullable=False),
        sa.Column("joined_at", timestamp_type, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("team_id", "user_id"),
    )
    op.create_table(
        "meetings",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("team_id", uuid_type, nullable=False),
        sa.Column("host_user_id", uuid_type),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("scheduled_at", timestamp_type),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column(
            "ai_intervention_level", sa.String(length=32), server_default="medium", nullable=False
        ),
        sa.Column("created_at", timestamp_type, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp_type, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["host_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_table(
        "meeting_participants",
        sa.Column("meeting_id", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("role", sa.String(length=32), server_default="participant", nullable=False),
        sa.Column(
            "attendance_status", sa.String(length=32), server_default="invited", nullable=False
        ),
        sa.Column("joined_at", timestamp_type),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("meeting_id", "user_id"),
    )
    op.create_table(
        "agenda_items",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("meeting_id", uuid_type, nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("created_at", timestamp_type, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id", "position", name="uq_agenda_meeting_position"),
    )


def downgrade() -> None:
    op.drop_table("agenda_items")
    op.drop_table("meeting_participants")
    op.drop_table("meetings")
    op.drop_table("team_members")
    op.drop_table("teams")
    op.drop_table("users")
