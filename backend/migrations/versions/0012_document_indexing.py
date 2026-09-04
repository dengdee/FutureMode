"""Track document versions and indexing state."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_document_indexing"
down_revision: str | None = "0011_documents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents", sa.Column("version", sa.Integer(), server_default="1", nullable=False)
    )
    op.add_column("documents", sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("documents", sa.Column("index_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "index_error")
    op.drop_column("documents", "indexed_at")
    op.drop_column("documents", "version")
