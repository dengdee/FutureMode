"""Prevent duplicate transcript ingestion requests."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_transcript_idempotency"
down_revision: str | None = "0016_version_storage_key"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("transcripts", sa.Column("idempotency_key", sa.String(length=128), nullable=True))
    op.create_unique_constraint(
        "uq_transcript_idempotency", "transcripts", ["meeting_id", "idempotency_key"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_transcript_idempotency", "transcripts", type_="unique")
    op.drop_column("transcripts", "idempotency_key")
