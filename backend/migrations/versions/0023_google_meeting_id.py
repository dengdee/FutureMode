"""Store the Google Meet context id used by the Add-on."""
from alembic import op

revision = "0023_google_meeting_id"
down_revision = "0022_preparation_messages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE meetings ADD COLUMN IF NOT EXISTS google_meeting_id VARCHAR(128)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_meetings_google_meeting_id ON meetings (google_meeting_id) WHERE google_meeting_id IS NOT NULL")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_meetings_google_meeting_id")
    op.execute("ALTER TABLE meetings DROP COLUMN IF EXISTS google_meeting_id")
