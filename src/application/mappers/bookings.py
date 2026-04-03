from src.application.dto.booking import BookingSchema
from src.core.domain.models import Booking as BookingDomain
from src.infrastructure.database.models import Booking as BookingDb

def bookings_domain_to_dto(b: BookingDomain)->BookingSchema:
    return BookingSchema(
        id=b.id,
        slotId=b.slot_id,
        userId=b.user_id,
        conferenceLink=b.conference_link,
        createdAt=b.creared_at,
    )

def bookings_db_to_domain(b: BookingDb)->BookingDomain:
    return BookingDomain(
        id=b.id,
        slot_id=b.slot_id,
        user_id=b.user_id,
        conference_link=b.conference_link,
        creared_at=b.created_at,
    )