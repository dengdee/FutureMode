"""Track document embedding retry attempts."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_document_retry"
down_revision: str | None = "0013_document_embeddings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents", sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False)
    )


def downgrade() -> None:
    op.drop_column("documents", "retry_count")
