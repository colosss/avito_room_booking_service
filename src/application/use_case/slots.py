from datetime import datetime, timedelta, timezone, date
from uuid import UUID, uuid4
from src.core.domain.models import Slot, Schedule

def generate_slots_for_date(schedule: Schedule, target_date: date)->list[Slot]:
    if target_date.isoweekday() not in schedule.days_of_week:
        return[]
    
    start_h, start_m=map(int, schedule.start_time.split(":"))
    end_h, end_m=map(int, schedule.end_time.split(":"))

    slot_start=datetime(target_date.year, target_date.month, target_date.day, start_h, start_m, tzinfo=timezone.utc)
    day_end=datetime(target_date.year, target_date.month, target_date.day, end_h, end_m, tzinfo=timezone.utc)

    slots=[]
    while slot_start+timedelta(minutes=30)<=day_end:
        slot_end=slot_start+timedelta(minutes=30)
        slots.append(Slot(id=uuid4(), room_id=schedule.room_id, start=slot_start, end=slot_end))
        slot_start=slot_end
    return slots

