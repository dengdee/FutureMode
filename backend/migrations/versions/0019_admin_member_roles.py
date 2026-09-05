"""Replace the retired owner role with admin without deleting memberships."""

from alembic import op

revision = "0019_admin_member_roles"
down_revision = "0018_team_invitations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE team_members SET role = 'admin' WHERE role = 'owner'")
    op.execute("UPDATE team_invitations SET role = 'admin' WHERE role = 'owner'")


def downgrade() -> None:
    raise RuntimeError("Role consolidation cannot infer which admins were formerly owners.")
