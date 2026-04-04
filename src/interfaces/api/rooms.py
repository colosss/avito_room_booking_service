from fastapi import APIRouter, Depends, HTTPException
from src.interfaces.api.dependencies import get_current_user, require_admin
from src.infrastructure.database.db_helper import db_helper
from src.infrastructure.database.repositories.rooms import RoomRepository
from src.application.use_case.rooms import (
    CreateRoomUseCase,
    ListRoomsUseCase
)
from src.application.dto.rooms import (
    RoomCreateDTO,
    RoomListShema,
    RoomSchema,
)
from src.application.mappers.rooms import rooms_domain_to_dto

router=APIRouter(tags=["Rooms"])

@router.post("/rooms/create", response_model=RoomSchema, status_code=201)
async def create_room(
    body: RoomCreateDTO,
    current_user:dict=Depends(require_admin),
    session=Depends(db_helper.session_dependency)):

    room=await CreateRoomUseCase(RoomRepository(session=session)).execute(
        body.name,
        body.description,
        body.capacity,
    )
    return rooms_domain_to_dto(room)

@router.get("/rooms/list", response_model=RoomListShema)
async def list_rooms(
    current_user: dict=Depends(get_current_user),
    session=Depends(db_helper.session_dependency)):

    rooms=await ListRoomsUseCase(RoomRepository(session=session)).execute()
    return RoomListShema(rooms=[rooms_domain_to_dto(r) for r in rooms])
