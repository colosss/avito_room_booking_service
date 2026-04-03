from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID

class ScheduleCreateDTO(BaseModel):
    daysOfWeek: list[int]
    startTime: str
    endTime: str
    
    @field_validator("daysOfWeek")
    @classmethod
    def validate_days(cls, v:list[int])->list[int]:
        if not v or any(d<1 or d>7 for d in v):
            raise ValueError("daysOfWeek must contain values from 1 to 7")
        return v
    
class ScheduleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    roomId: UUID
    daysOfWeek: list[int]
    startTime: str
    endTime: str