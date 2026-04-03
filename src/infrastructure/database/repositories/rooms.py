from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.infrastructure.database.models import Room as RoomModel
from src.core.repositories import AbstractRoomRepository
from src.core.domain.models import Room
from typing import Optional, Sequence
from uuid import UUID
import uuid
from src.application.mappers.rooms import rooms_db_to_domain

class RoomRepository(AbstractRoomRepository):
    def __init__(self, session: AsyncSession):
        self.session=session

    async def create(self, name: str, description: Optional[str], capacity: Optional[int])->Room:
        room=RoomModel(id=uuid.uuid4(), name=name, description=description, capacity=capacity)
        self.session.add(room)
        await self.session.commit()
        await self.session.refresh(room)
        return rooms_db_to_domain(room)
    
    async def get_list(self)->Sequence[Room]:
        result=await self.session.execute(select(RoomModel))
        rooms=result.scalars().all()
        return [rooms_db_to_domain(r) for r in rooms]
    
    async def get_by_id(self, room_id: UUID)->Optional[Room]:
        room=await self.session.get(RoomModel, room_id)
        if not room:
            return None
        return rooms_db_to_domain(room)