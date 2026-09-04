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
