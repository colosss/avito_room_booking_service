from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class SlotSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    roomId: UUID
    start: datetime
    end: datetime
class SlotListSchema(BaseModel):
    slots: list[SlotSchema]