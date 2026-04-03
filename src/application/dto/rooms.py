from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class RoomCreateDTO(BaseModel):
    name:str
    description: Optional[str]=None
    capacity: Optional[int]=None

class RoomSchema(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: Optional[str]
    capacity: Optional[int]
    createdAt: Optional[datetime]

class RoomListShema(BaseModel):
    rooms: list[RoomSchema]