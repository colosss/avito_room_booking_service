from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.infrastructure.database.models import Room as RoomModel
from src.core.repositories import AbstractRoomRepository
from src.core.domain.models import Room
from typing import Optional, Sequence
from uuid import UUID
import uuid

class RoomRepository(AbstractRoomRepository):
    def __init__(self, session: AsyncSession):
        self.session=session

    async def create(self, name: str, description: Optional[str], capacity: Optional[int])->Room:
        room=RoomModel(id=uuid.uuid4(), name=name, description=description, capacity=capacity)
        self.session.add(room)
        await self.session.commit()
        await self.session.refresh(room)
        return Room(id=room.id, name=room.name, description=room.descriotion, capacity=room.capacity)