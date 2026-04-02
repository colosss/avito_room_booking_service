from abc import ABC, abstractmethod
from typing import Optional, Sequence
from uuid import UUID
from datetime import date as date_type
from src.core.domain.models import (
    User,
    Room,
    Schedule,
    Slot,
    Booking,
)

class AbstractUserRepository(ABC):
    
    @abstractmethod
    async def get_by_id(self, user_id: UUID)->Optional[User]: ...

    @abstractmethod
    async def get_by_email(self, email: str)->Optional[User]: ...

    @abstractmethod
    async def create(self, email: str, role: str, hashed_password: Optional[str])->User: ...

    @abstractmethod
    async def get_or_create_dummy(self, user_id: UUID, role: str)->User: ...

class AbstractRoomRepository(ABC):

    @abstractmethod
    async def create(self, name: str, description: Optional[str], capacity: Optional[int])->Room: ...

    @abstractmethod
    async def get_list(self)->Sequence[Room]: ...

    @abstractmethod
    async def get_by_id(self, room_id: UUID)->Optional[Room]: ...


class AbstractScheduleRepository(ABC):
    
    @abstractmethod
    async def create(self, room_id: UUID, days_of_week: list[int], start_time: str, end_time: str)->Schedule: ...

    @abstractmethod
    async def get_by_room_id(self, room_id: UUID)->Optional[Schedule]: ...

class AbstractSlotRepository(ABC):

    @abstractmethod
    async def bulk_upsert(self, slots: list[Slot])->None: ...

    @abstractmethod
    async def get_by_id(self, slot_id: UUID)->Optional[Slot]: ...

    @abstractmethod
    async def get_available_by_room_and_date(self, room_id: UUID, date: date_type)->Schedule: ...


class AbstractBookingRepository(ABC):

    @abstractmethod
    async def create(self, slot_id: UUID, user_id: UUID, conference_link: Optional[str])->Booking: ...

    @abstractmethod
    async def get_by_id(self, booking_id: UUID)->Optional[Booking]: ...

    @abstractmethod
    async def cancel(self, booking_id:UUID)->Booking: ...

    @abstractmethod
    async def get_my_bookings(self, user_id: UUID)->Sequence[Booking]: ...

    @abstractmethod
    async def get_all(self, page: int, page_size: int)->tuple[Sequence[Booking]]: ...

    @abstractmethod
    async def get_active_by_slot_id(self, slot_id: UUID)->Optional[Booking]: ...