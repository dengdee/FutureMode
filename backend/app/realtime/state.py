"""In-process compare-and-set storage for meeting state."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID

from app.schemas.events import MeetingStateSnapshot


class StateVersionConflict(Exception):
    """Raised when a state write does not use the current state version."""


class StateVersionStore:
    """Provide atomic state updates for one application process.

    A deployment with multiple API instances must replace or coordinate this store
    through the database and pub/sub layer before it can be used as the authority.
    """

    def __init__(self) -> None:
        self._snapshots: dict[UUID, MeetingStateSnapshot] = {}
        self._lock = asyncio.Lock()

    async def get(self, meeting_id: UUID) -> MeetingStateSnapshot:
        async with self._lock:
            snapshot = self._snapshots.get(meeting_id)
            if snapshot is None:
                return MeetingStateSnapshot(
                    meeting_id=meeting_id,
                    state_version=0,
                    state={},
                    updated_at=None,
                )
            return snapshot.model_copy(deep=True)

    async def update(
        self,
        *,
        meeting_id: UUID,
        expected_state_version: int,
        state: dict[str, object],
        updated_by: UUID,
    ) -> MeetingStateSnapshot:
        async with self._lock:
            current = self._snapshots.get(meeting_id)
            current_version = current.state_version if current is not None else 0
            if expected_state_version != current_version:
                raise StateVersionConflict
            snapshot = MeetingStateSnapshot(
                meeting_id=meeting_id,
                state_version=current_version + 1,
                state=state,
                updated_at=datetime.now(UTC),
            )
            self._snapshots[meeting_id] = snapshot
            return snapshot.model_copy(deep=True)
