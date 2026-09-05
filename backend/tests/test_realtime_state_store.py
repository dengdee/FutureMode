import asyncio
from uuid import uuid4

import pytest

from app.realtime.state import StateVersionConflict, StateVersionStore


def test_state_store_creates_initial_snapshot_at_version_one() -> None:
    async def scenario() -> None:
        meeting_id = uuid4()
        store = StateVersionStore()

        snapshot = await store.update(
            meeting_id=meeting_id,
            expected_state_version=0,
            state={"topic": "kickoff"},
            updated_by=uuid4(),
        )

        assert snapshot.meeting_id == meeting_id
        assert snapshot.state_version == 1
        assert snapshot.state == {"topic": "kickoff"}

    asyncio.run(scenario())


def test_state_store_rejects_a_stale_state_version_without_overwriting_state() -> None:
    async def scenario() -> None:
        meeting_id = uuid4()
        store = StateVersionStore()
        await store.update(
            meeting_id=meeting_id,
            expected_state_version=0,
            state={"topic": "current"},
            updated_by=uuid4(),
        )

        with pytest.raises(StateVersionConflict):
            await store.update(
                meeting_id=meeting_id,
                expected_state_version=0,
                state={"topic": "stale"},
                updated_by=uuid4(),
            )

        snapshot = await store.get(meeting_id)
        assert snapshot.state_version == 1
        assert snapshot.state == {"topic": "current"}

    asyncio.run(scenario())


def test_concurrent_updates_with_the_same_version_have_exactly_one_winner() -> None:
    async def scenario() -> None:
        meeting_id = uuid4()
        store = StateVersionStore()

        async def update(topic: str) -> str:
            try:
                await store.update(
                    meeting_id=meeting_id,
                    expected_state_version=0,
                    state={"topic": topic},
                    updated_by=uuid4(),
                )
                return "updated"
            except StateVersionConflict:
                return "conflict"

        outcomes = await asyncio.gather(update("first"), update("second"))

        assert sorted(outcomes) == ["conflict", "updated"]
        assert (await store.get(meeting_id)).state_version == 1

    asyncio.run(scenario())
