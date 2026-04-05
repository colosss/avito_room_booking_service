import re
from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID

TIME_RE = re.compile(r"^([01][0-9]|2[0-3]):[0-5][0-9]$")
# TIME_RE = re.compile(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")


class ScheduleCreateDTO(BaseModel):
    daysOfWeek: list[int]
    startTime: str
    endTime: str

    @field_validator("daysOfWeek")
    @classmethod
    def validate_days(cls, v: list[int]) -> list[int]:
        if not v or any(d < 1 or d > 7 for d in v):
            raise ValueError("daysOfWeek must contain values from 1 to 7")
        return v

    @field_validator("startTime", "endTime")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        if not TIME_RE.match(v):
            raise ValueError("time must be in HH:MM format (00:00–23:59)")
        return v

class ScheduleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    roomId: UUID
    daysOfWeek: list[int]
    startTime: str
    endTime: str