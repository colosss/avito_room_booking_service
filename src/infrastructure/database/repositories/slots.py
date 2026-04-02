from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, not_, exists
from sqlalchemy.dialects.postgresql import insert as pg_insert
from src.infrastructure.database.models import Slot as SlotModel, Booking as BookingModel
from src.core.repositories import AbstractSlotRepository
from src.core.domain.models import Slot
from typing import Optional, Sequence
from uuid import UUID
import uuid as uuid_module
from datetime import datetime, timezone, date as date_type

SLOT_NAMESPACE=UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

def make_slot_uuid(room_id:UUID, slot_start: datetime)->UUID:
    name=f"{room_id}:{slot_start.isoformat()}"
    return uuid_module.uuid5(SLOT_NAMESPACE, name)

class SlotRepository(AbstractSlotRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_upsert(self, slots: list[Slot]) -> None:
        if not slots:
            return
        values = [{"id": s.id, "room_id": s.room_id, "start": s.start, "end": s.end} for s in slots]
        stmt = pg_insert(SlotModel).values(values).on_conflict_do_nothing(index_elements=["id"])
        await self.session.execute(stmt)
        await self.session.commit()
    
    async def get_by_id(self, slot_id: UUID) -> Optional[Slot]:
        s = await self.session.get(SlotModel, slot_id)
        return Slot(id=s.id, room_id=s.room_id, start=s.start, end=s.end) if s else None
    
    async def get_available_by_room_and_date(self, room_id: UUID, date: date_type) -> Sequence[Slot]:
        active_booking_subq = (
            select(BookingModel.slot_id)
            .where(BookingModel.status == "active")
            .scalar_subquery()
        )
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
        stmt = (
            select(SlotModel)
            .where(
                SlotModel.room_id == room_id,
                SlotModel.start >= day_start,
                SlotModel.start <= day_end,
                SlotModel.id.not_in(active_booking_subq),
            )
            .order_by(SlotModel.start)
        )
        result = await self.session.execute(stmt)
        return [Slot(id=s.id, room_id=s.room_id, start=s.start, end=s.end)
            for s in result.scalars().all()]