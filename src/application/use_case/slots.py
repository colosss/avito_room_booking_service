from datetime import datetime, timedelta, timezone, date as date_type
from uuid import UUID
from src.core.domain.models import Slot, Schedule
from src.core.repositories import (
    AbstractSlotRepository,
    AbstractScheduleRepository,
    AbstractRoomRepository,
)
from src.infrastructure.database.repositories.slots import make_slot_uuid
from src.infrastructure.cache.redis_client import get_redis
import json

SLOTS_CACHE_TTL = 60


def generate_slots_for_date(schedule: Schedule, target_date: date_type) -> list[Slot]:
    if target_date.isoweekday() not in schedule.days_of_week:
        return []

    start_h, start_m = map(int, schedule.start_time.split(":"))
    end_h, end_m = map(int, schedule.end_time.split(":"))

    slot_start = datetime(target_date.year, target_date.month, target_date.day, start_h, start_m, tzinfo=timezone.utc)
    day_end = datetime(target_date.year, target_date.month, target_date.day, end_h, end_m, tzinfo=timezone.utc)

    slots = []
    while slot_start + timedelta(minutes=30) <= day_end:
        slot_end = slot_start + timedelta(minutes=30)
        slots.append(Slot(
            id=make_slot_uuid(schedule.room_id, slot_start),
            room_id=schedule.room_id,
            start=slot_start,
            end=slot_end,
        ))
        slot_start = slot_end
    return slots


class GetAvailableSlotsUseCase:
    def __init__(self, room_repo: AbstractRoomRepository, schedule_repo: AbstractScheduleRepository, slot_repo: AbstractSlotRepository):
        self._rooms = room_repo
        self._schedules = schedule_repo
        self._slots = slot_repo

    def _cache_key(self, room_id: UUID, date: date_type) -> str:
        return f"slots:{room_id}:{date.isoformat()}"
    
    def _deserialize_slots(self, raw: list[dict]) -> list[Slot]:
        return [
            Slot(
                id=UUID(s["id"]),
                room_id=UUID(s["roomId"]),
                start=datetime.fromisoformat(s["start"]),
                end=datetime.fromisoformat(s["end"]),
            )
            for s in raw
        ]

    async def execute(self, room_id: UUID, target_date: date_type) -> list[Slot]:
        redis = await get_redis()
        key = self._cache_key(room_id, target_date)
        cached = await redis.get(key)

        if cached is not None:
            return self._deserialize_slots(json.loads(cached))
        
        async with redis.lock(f"lock:slots:{room_id}:{target_date.isoformat()}", timeout=10):
            cached = await redis.get(key)
            if cached is not None:
                return self._deserialize_slots(json.loads(cached))
            
            room = await self._rooms.get_by_id(room_id)
            if not room:
                raise ValueError("ROOM_NOT_FOUND")

            schedule = await self._schedules.get_by_room_id(room_id)
            if not schedule:
                await redis.setex(key, SLOTS_CACHE_TTL, json.dumps([]))
                return []

            generated = generate_slots_for_date(schedule, target_date)
            if generated:
                await self._slots.bulk_upsert(generated)

            slots = await self._slots.get_available_by_room_and_date(room_id, target_date)

            serialized = [
                {
                    "id": str(s.id),
                    "roomId": str(s.room_id),
                    "start": s.start.isoformat(),
                    "end": s.end.isoformat(),
                }
                for s in slots
            ]

            await redis.setex(key, SLOTS_CACHE_TTL, json.dumps(serialized))
            return slots