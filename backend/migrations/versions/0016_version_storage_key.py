"""Link document versions to original R2 objects."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_version_storage_key"
down_revision: str | None = "0015_document_versions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "document_versions", sa.Column("storage_key", sa.String(length=1024), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("document_versions", "storage_key")
