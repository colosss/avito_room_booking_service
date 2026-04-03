from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class BookingCreateDTO(BaseModel):
    slotId: UUID
    createConferenceLink: bool = False
class BookingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    slotId: UUID
    userId: UUID
    status: str
    conferenceLink: Optional[str]
    createdAt: Optional[datetime]
class PaginationSchema(BaseModel):
    page: int
    pageSize: int
    total: int
class BookingListSchema(BaseModel):
    bookings: list[BookingSchema]
    pagination: PaginationSchema
class MyBookingListSchema(BaseModel):
    bookings: list[BookingSchema]