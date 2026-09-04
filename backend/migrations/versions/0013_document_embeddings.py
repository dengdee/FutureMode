"""Add pgvector embeddings to document chunks."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0013_document_embeddings"
down_revision: str | None = "0012_document_indexing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("document_chunks", sa.Column("embedding", Vector(1536), nullable=True))


def downgrade() -> None:
    op.drop_column("document_chunks", "embedding")
