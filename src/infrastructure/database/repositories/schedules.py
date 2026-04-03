from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.infrastructure.database.models import Schedule as ScheduleModel
from src.core.repositories import AbstractScheduleRepository
from src.core.domain.models import Schedule
from typing import Optional
from uuid import UUID
import uuid
from src.application.mappers.schedules import schedules_db_to_domain

class ScheduleRepository(AbstractScheduleRepository):
    def __init__(self, session: AsyncSession):
        self.session=session

    async def create(self, room_id: UUID, days_of_week: list[int], start_time: str, end_time: str) -> Schedule:
        s = ScheduleModel(id=uuid.uuid4(), room_id=room_id, days_of_week=days_of_week, start_time=start_time, end_time=end_time) 
        self.session.add(s)
        await self.session.commit()
        await self.session.refresh(s)
        return schedules_db_to_domain(s=s)
    
    async def get_by_room_id(self, room_id: UUID) -> Optional[Schedule]:
        result = await self.session.execute(select(ScheduleModel).where(ScheduleModel.room_id == room_id))
        s = result.scalar_one_or_none()
        if not s:
            return None
        return schedules_db_to_domain(s=s)