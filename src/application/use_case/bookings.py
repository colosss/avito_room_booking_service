from datetime import datetime, timezone
from uuid import UUID
from src.core.repositories import (
    AbstractBookingRepository,
    AbstractSlotRepository,
)
from src.infrastructure.cache.redis_client import invalidate_slots_cache
import uuid


class CreateBookingUseCase:
    def __init__(self, bookint_repo: AbstractBookingRepository, slot_repo: AbstractSlotRepository):
        self._bookings=bookint_repo
        self._slots=slot_repo
    
    async def execute(self, slot_id: UUID, user_id: UUID, create_conference_link: bool=False):
        slot=await self._slots.get_by_id(slot_id=slot_id)
        if not slot:
            raise ValueError("SLOT_NOT_FOUND")
        if slot.start<datetime.now(timezone.utc):
            raise ValueError("INVALID_REQUEST:slot is in the past")
        existing=await self._bookings.get_active_by_slot_id(slot_id=slot_id)
        if existing:
            raise ValueError("SLOT_ALREADY_BOOKED")
        conference_link=None
        if create_conference_link:
            conference_link=await self._get_conference_link()
        booking = await self._bookings.create(slot_id=slot_id, user_id=user_id, conference_link=conference_link)
        # Инвалидируем кэш слотов для этой комнаты и даты
        await invalidate_slots_cache(slot.room_id, slot.start.date())
        return booking

    async def _get_conference_link(self)->str:
        return f"https://conference.exemple.com/room/{uuid.uuid4()}"
    
class CancelBookingUseCase:
    def __init__(self, booking_repo: AbstractBookingRepository, slot_repo: AbstractSlotRepository):
        self._repo = booking_repo
        self._slots = slot_repo

    async def execute(self, booking_id: UUID, user_id: UUID):
        booking = await self._repo.get_by_id(booking_id=booking_id)
        if not booking:
            raise ValueError("BOOKING_NOT_FOUND")
        if str(booking.user_id) != str(user_id):
            raise ValueError("FORBIDDEN")
        if booking.status == "cancelled":
            return booking
        cancelled = await self._repo.cancel(booking_id=booking_id)
        slot = await self._slots.get_by_id(slot_id=booking.slot_id)
        if slot:
            await invalidate_slots_cache(slot.room_id, slot.start.date())
        return cancelled


class GetMyBookingUseCase:
    def __init__(self, booking_repo: AbstractBookingRepository):
        self._repo=booking_repo

    async def execute(self, user_id:UUID):
        return await self._repo.get_my_bookings(user_id)
    
class ListAllBookingUseCase:
    def __init__(self, booking_repo:AbstractBookingRepository):
        self._repo=booking_repo

    async def execute(self, page: int, page_size: int):
        return await self._repo.get_all(page=page, page_size=page_size)
    

