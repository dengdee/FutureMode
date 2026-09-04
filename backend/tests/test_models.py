from sqlalchemy import inspect

from app.db.base import Base


def test_core_tables_are_registered() -> None:
    assert {
        "users",
        "teams",
        "team_members",
        "meetings",
        "meeting_participants",
        "agenda_items",
        "meeting_states",
        "meeting_event_cursors",
        "bot_sessions",
        "voice_requests",
        "transcripts",
        "ai_suggestions",
        "suggestion_votes",
    }.issubset(Base.metadata.tables)


def test_join_tables_have_composite_primary_keys() -> None:
    for table_name in ("team_members", "meeting_participants"):
        table = Base.metadata.tables[table_name]
        assert len(inspect(table).primary_key.columns) == 2


def test_agenda_positions_are_unique_per_meeting() -> None:
    table = Base.metadata.tables["agenda_items"]
    assert any(
        constraint.name == "uq_agenda_meeting_position" for constraint in table.constraints
    )


def test_core_foreign_keys_use_safe_delete_actions() -> None:
    meetings = Base.metadata.tables["meetings"]
    fk_actions = {fk.ondelete for fk in meetings.foreign_keys}
    assert fk_actions == {"CASCADE", "SET NULL"}


def test_realtime_tables_have_expected_keys() -> None:
    assert len(inspect(Base.metadata.tables["meeting_states"]).primary_key.columns) == 1
    assert len(inspect(Base.metadata.tables["meeting_event_cursors"]).primary_key.columns) == 2


def test_bot_session_is_one_per_meeting() -> None:
    table = Base.metadata.tables["bot_sessions"]
    assert any(c.name == "uq_bot_sessions_meeting" for c in table.constraints)
