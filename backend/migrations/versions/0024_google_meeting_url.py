"""Persist the full Google Meet URL on meetings."""

from alembic import op


revision = "0024_google_meeting_url"
down_revision = "0023_google_meeting_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE meetings ADD COLUMN IF NOT EXISTS google_meeting_url TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE meetings DROP COLUMN IF EXISTS google_meeting_url")
