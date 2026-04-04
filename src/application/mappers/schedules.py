from src.application.dto.schedule import ScheduleSchema
from src.core.domain.models import Schedule as ScheduleDomain
from src.infrastructure.database.models import Schedule as ScheduleDb

def schedules_domain_to_dto(s: ScheduleDomain)->ScheduleSchema:
    return ScheduleSchema(
        id=s.id,
        roomId=s.room_id,
        daysOfWeek=s.days_of_week,
        startTime=s.start_time,
        endTime=s.end_time,
    )

def schedules_db_to_domain(s: ScheduleDb)->ScheduleDomain:
    return ScheduleDomain(
        id=s.id,
        room_id=s.room_id,
        days_of_week=s.days_of_week,
        start_time=s.start_time,
        end_time=s.end_time,
    )
