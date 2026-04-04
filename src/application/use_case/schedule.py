from uuid import UUID
from src.core.repositories import AbstractRoomRepository, AbstractScheduleRepository

def _time_to_minutes(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m

class CreateScheduleUseCase:
    def __init__(self, room_repo: AbstractRoomRepository, schedule_repo: AbstractScheduleRepository):
        self._rooms = room_repo
        self._schedules = schedule_repo

    async def execute(self, room_id: UUID, days_of_week: list[int], start_time: str, end_time: str):
        # if not days_of_week or any(d < 1 or d > 7 for d in days_of_week):
        #     raise ValueError("INVALID_REQUEST:invalid daysOfWeek")

        if _time_to_minutes(start_time) >= _time_to_minutes(end_time):
            raise ValueError("INVALID_REQUEST:startTime must be before endTime")

        if _time_to_minutes(end_time) - _time_to_minutes(start_time) < 30:
            raise ValueError("INVALID_REQUEST:time range must be at least 30 minutes")

        room = await self._rooms.get_by_id(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")

        existing = await self._schedules.get_by_room_id(room_id)
        if existing:
            raise ValueError("SCHEDULE_EXISTS")

        return await self._schedules.create(room_id, days_of_week, start_time, end_time)
