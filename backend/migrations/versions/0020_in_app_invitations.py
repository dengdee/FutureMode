"""Allow invitation history while retaining one pending invitation per recipient."""

from alembic import op

revision = "0020_in_app_invitations"
down_revision = "0019_admin_member_roles"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_team_invite_pending "
        "ON team_invitations (team_id, email) WHERE status = 'pending'"
    )
    op.execute("ALTER TABLE team_invitations DROP CONSTRAINT IF EXISTS uq_team_invite_email_status")


def downgrade():
    raise RuntimeError("Invitation history must be reviewed before restoring the old constraint.")
