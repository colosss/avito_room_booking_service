from src.application.dto.slots import SlotListSchema, SlotSchema
from src.core.domain.models import Slot as SlotDomain
from src.infrastructure.database.models import Slot as SlotDb


def slots_domain_to_dto(s: SlotDomain)->SlotSchema:
    return SlotSchema(
        id=s.id,
        roomId=s.room_id,
        start=s.start,
        end=s.end,
    )

def slots_db_to_domain(s: SlotDb)->slots_domain_to_dto:
    return SlotDomain(
        id=s.id,
        room_id=s.room_id,
        start=s.start,
        end=s.end,
    )

def slots_domain_to_list(s: SlotDomain):
    return {"id": s.id,
            "room_id": s.room_id,
            "start": s.start,
            "end": s.end}