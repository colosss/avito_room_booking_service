from src.application.dto.rooms import RoomSchema
from src.core.domain.models import Room as RoomDomain
from src.infrastructure.database.models import Room as RoomDb

def rooms_domain_to_dto(r: RoomDomain)->RoomSchema:
    return RoomSchema(
        id=r.id, 
        name=r.name, 
        description=r.description, 
        capacity=r.capacity, 
        createdAt=r.created_at,
        )

def rooms_db_to_domain(r: RoomDb)->RoomDomain:
    return RoomDomain(
        id=r.id,
        name=r.name,
        description=r.descriotion,
        capacity=r.capacity,
        created_at=r.created_at,
    )