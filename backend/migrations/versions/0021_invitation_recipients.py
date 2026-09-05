"""Bind new invitations to registered users; preserve legacy email invitations unassigned."""
from alembic import op

revision = "0021_invitation_recipients"
down_revision = "0020_in_app_invitations"
branch_labels = None
depends_on = None

STATEMENTS = (
    "ALTER TABLE team_invitations ADD COLUMN IF NOT EXISTS recipient_user_id UUID "
    "REFERENCES users(id) ON DELETE CASCADE",
    "ALTER TABLE team_invitations ADD COLUMN IF NOT EXISTS recipient_name VARCHAR(255)",
    "ALTER TABLE team_invitations ALTER COLUMN email DROP NOT NULL",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_team_invite_recipient_pending "
    "ON team_invitations(team_id, recipient_user_id) "
    "WHERE status = 'pending' AND recipient_user_id IS NOT NULL",
)


def upgrade():
    for statement in STATEMENTS:
        op.execute(statement)


def downgrade():
    raise RuntimeError("Account invitations cannot be downgraded to unverified email matching.")
