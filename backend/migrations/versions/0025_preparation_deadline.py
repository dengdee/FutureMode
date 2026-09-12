"""Persist the required preparation discussion deadline on meetings."""

from alembic import op


revision = "0025_preparation_deadline"
down_revision = "0024_google_meeting_url"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE meetings ADD COLUMN IF NOT EXISTS preparation_deadline TIMESTAMPTZ")


def downgrade() -> None:
    op.execute("ALTER TABLE meetings DROP COLUMN IF EXISTS preparation_deadline")
