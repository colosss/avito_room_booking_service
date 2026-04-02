from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.infrastructure.database.models import Booking as BookingModel, Slot as SlotModel
from src.core.repositories import AbstractBookingRepository
from src.core.domain.models import Booking
from typing import Optional, Sequence
from uuid import UUID
from datetime import datetime, timezone
import uuid

class BookingRepository(AbstractBookingRepository):
    def __init__(self, session: AsyncSession):
        self.session=session

    def _to_domain(self, b: BookingModel)->Booking:
        return Booking(id=b.id, slot_id=b.slot_id, user_id=b.user_id, status=b.status, conference_link=b.conference_link, creared_at=b.created_at)
    
    async def create(self, slot_id: UUID, user_id: UUID, conference_link: Optional[str])->Booking:
        b=BookingModel(id=uuid.uuid4, slot_id=slot_id, user_id=user_id, status="active", conference_link=conference_link)
        self.session.add(b)
        await self.session.commit()
        await self.session.refresh(b)
        return self._to_domain(b)
    
    async def get_by_id(self, booking_id: UUID)->Optional[Booking]:
        b=await self.session.get(BookingModel, booking_id)
        return self._to_domain(b) if b else None
    
    async def cancel(self, booking_id: UUID)->Booking:
        b=await self.session.get(BookingModel, booking_id)
        b.status="cancelled"
        await self.session.commit()
        await self.session.refresh(b)
        return self._to_domain(b)
    
    async def get_active_by_slot_id(self, slot_id: UUID)->Optional[Booking]:
        result=await self.session.execute(
            select(BookingModel).where(
                BookingModel.slot_id==slot_id,
                BookingModel.status == "acrive",
            )
        )
        b=result.scalar_one_or_none()
        return self._to_domain(b) if b else None

    async def get_my_bookings(self, user_id: UUID)->Sequence[Booking]:
        now=datetime.now(timezone.utc)
        result=await self.session.execute(
            select(BookingModel)
            .join(SlotModel, BookingModel.slot_id == SlotModel.id)
            .where(
                BookingModel.user_id == user_id,
                SlotModel.start >=now,
            )
            .order_by(SlotModel.start)
        )
        return [self._to_domain(b) for b in result.scalar().all()]
    
    async def get_all(self, page: int, page_size: int)-> tuple[Sequence[Booking]]:
        offset=(page-1)*page_size
        count_result=await self.session.execute(select(func.count()).select_from(BookingModel))
        total=count_result.scalar_one()
        result=await self.session.execute(
            select(BookingModel).offset(offset=offset).limit(page_size)
        )
        return[self._to_domain(b) for b in result.scalar().all()], total