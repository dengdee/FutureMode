"""Cross-instance realtime fan-out through Upstash Redis pub/sub."""

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID, uuid4

from redis.asyncio import Redis

from app.schemas.events import MeetingEvent

CHANNEL = "proximate:realtime"
PRESENCE_TTL_SECONDS = 90


@dataclass(frozen=True)
class BrokerEvent:
    """A durable event notification delivered to a Vercel function instance."""

    origin_id: UUID
    event: MeetingEvent
    recipient_user_id: UUID | None


class RedisRealtimeBroker:
    """Publish events between Vercel instances; PostgreSQL remains the authority."""

    def __init__(self, url: str, *, origin_id: UUID | None = None) -> None:
        self._redis = Redis.from_url(url, decode_responses=True)
        self.origin_id = origin_id or uuid4()

    async def publish(
        self, event: MeetingEvent, *, recipient_user_id: UUID | None = None
    ) -> None:
        await self._redis.publish(
            CHANNEL,
            json.dumps(
                {
                    "origin_id": str(self.origin_id),
                    "event": event.model_dump(mode="json"),
                    "recipient_user_id": str(recipient_user_id) if recipient_user_id else None,
                }
            ),
        )

    async def subscribe(self) -> AsyncIterator[BrokerEvent]:
        """Yield notifications from other instances for local socket delivery."""
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(CHANNEL)
        try:
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message is None:
                    await asyncio.sleep(0)
                    continue
                raw = message.get("data")
                if not isinstance(raw, str):
                    continue
                parsed = json.loads(raw)
                origin_id = UUID(parsed["origin_id"])
                if origin_id == self.origin_id:
                    continue
                recipient = parsed.get("recipient_user_id")
                yield BrokerEvent(
                    origin_id=origin_id,
                    event=MeetingEvent.model_validate(parsed["event"]),
                    recipient_user_id=UUID(recipient) if recipient else None,
                )
        finally:
            await pubsub.unsubscribe(CHANNEL)
            await pubsub.aclose()

    async def join_presence(
        self, meeting_id: UUID, user_id: UUID, connection_id: UUID
    ) -> bool:
        """Register one socket and return true only for a user's first global connection."""
        key = _presence_key(meeting_id)
        joined = await self._redis.eval(
            """
            local exists = 0
            for _, value in ipairs(redis.call('HVALS', KEYS[1])) do
                if value == ARGV[1] then exists = 1 end
            end
            redis.call('HSET', KEYS[1], ARGV[2], ARGV[1])
            redis.call('EXPIRE', KEYS[1], ARGV[3])
            return exists == 0 and 1 or 0
            """,
            1,
            key,
            str(user_id),
            str(connection_id),
            PRESENCE_TTL_SECONDS,
        )
        return bool(joined)

    async def leave_presence(
        self, meeting_id: UUID, user_id: UUID, connection_id: UUID
    ) -> bool:
        """Remove one socket and return true only for the user's last global connection."""
        key = _presence_key(meeting_id)
        left = await self._redis.eval(
            """
            redis.call('HDEL', KEYS[1], ARGV[2])
            local exists = 0
            for _, value in ipairs(redis.call('HVALS', KEYS[1])) do
                if value == ARGV[1] then exists = 1 end
            end
            if redis.call('HLEN', KEYS[1]) == 0 then
                redis.call('DEL', KEYS[1])
            else
                redis.call('EXPIRE', KEYS[1], ARGV[3])
            end
            return exists == 0 and 1 or 0
            """,
            1,
            key,
            str(user_id),
            str(connection_id),
            PRESENCE_TTL_SECONDS,
        )
        return bool(left)

    async def close(self) -> None:
        await self._redis.aclose()


def _presence_key(meeting_id: UUID) -> str:
    return f"proximate:presence:{meeting_id}"
