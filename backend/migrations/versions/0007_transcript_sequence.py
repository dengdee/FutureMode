"""Ensure transcript sequence is unique per meeting."""

from collections.abc import Sequence

from alembic import op

revision: str = "0007_transcript_sequence"
down_revision: str | None = "0006_ai_suggestions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("uq_transcript_sequence", "transcripts", type_="unique")
    op.create_unique_constraint("uq_transcript_sequence", "transcripts", ["meeting_id", "sequence"])


def downgrade() -> None:
    op.drop_constraint("uq_transcript_sequence", "transcripts", type_="unique")
    op.create_unique_constraint(
        "uq_transcript_sequence", "transcripts", ["meeting_id", "speaker_user_id", "sequence"]
    )
