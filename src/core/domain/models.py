from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

@dataclass
class User:
    id: UUID
    email: str
    role: str
    hashed_password: Optional[str]
    created_at: Optional[datetime]

@dataclass
class Room:
    id:UUID
    name:str
    description: Optional[str]
    capacity: Optional[int]
    created_at: Optional[datetime]

@dataclass
class Schedule:
    id: UUID
    room_id: UUID
    days_of_week: list[int]
    start_time: str
    end_time:str

@dataclass
class Slot:
    id: UUID
    room_id: UUID
    start: datetime
    end: datetime
    
@dataclass
class Booking:
    id:UUID
    slot_id:UUID
    user_id:UUID
    status: str
    conference_link:Optional[str]
    creared_at:Optional[datetime]

