from src.application.dto.auth import UserSchema
from src.core.domain.models import User as UserDomain
from src.infrastructure.database.models import User as UserDb

def users_domain_to_dto(u: UserDomain)->UserSchema:
    return UserSchema(
        id=u.id,
        email=u.email,
        role=u.role,
    )

def users_db_to_domain(u: UserDb)->UserDomain:
    return UserDomain(
        id=u.id,
        email=u.email,
        role=u.role,
        hashed_password=u.hashed_password,
        created_at=u.created_at, 
    )