from uuid import UUID
from src.core.repositories import AbstractRoomRepository, AbstractScheduleRepository

class CreateScheduleUseCase:
    def __init__(self, room_repo: AbstractRoomRepository, schedule_repo: AbstractScheduleRepository):
        self._rooms = room_repo
        self._schedules = schedule_repo

    async def execute(self, room_id: UUID, days_of_week: list[int], start_time: str, end_time: str):
        if not days_of_week or any(d < 1 or d > 7 for d in days_of_week):
            raise ValueError("INVALID_REQUEST:invalid daysOfWeek")
        room = await self._rooms.get_by_id(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        existing = await self._schedules.get_by_room_id(room_id)
        if existing:
            raise ValueError("SCHEDULE_EXISTS")
        return await self._schedules.create(room_id, days_of_week, start_time, end_time)