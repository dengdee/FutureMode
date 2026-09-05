"""Store pre-meeting AI conversation messages."""
from alembic import op

revision = "0022_preparation_messages"
down_revision = "0021_invitation_recipients"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS preparation_messages (
        id UUID PRIMARY KEY,
        meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        role VARCHAR(16) NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_preparation_messages_meeting_user ON preparation_messages (meeting_id, user_id, created_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS preparation_messages")
