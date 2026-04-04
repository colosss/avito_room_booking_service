from fastapi import APIRouter, Depends, HTTPException, Query
from src.interfaces.api.dependencies import get_current_user
from src.infrastructure.database.repositories.rooms import RoomRepository
from src.infrastructure.database.repositories.schedules import ScheduleRepository
from src.infrastructure.database.repositories.slots import SlotRepository
from src.application.use_case.slots import GetAvailableSlotsUseCase
from src.application.dto.slots import SlotListSchema
from uuid import UUID
from datetime import date
from src.application.mappers.slots import slots_domain_to_dto
from src.infrastructure.database.db_helper import db_helper

router=APIRouter(tags=["Slots"])

@router.get("/rooms/{roomId}/slots/list", response_model=SlotListSchema)
async def list_slots(
    roomId:UUID,
    date: date=Query(...),
    current_user: dict=Depends(get_current_user),
    session=Depends(db_helper.session_dependency),
):
    try:
        slots=await GetAvailableSlotsUseCase(
            room_repo=RoomRepository(session=session),
            schedule_repo=ScheduleRepository(session=session),
            slot_repo=SlotRepository(session=session),
        ).execute(room_id=roomId, target_date=date)
    except ValueError as e:
        code = str(e).split(":")[0]
        status_map = {"ROOM_NOT_FOUND": 404}
        raise HTTPException(status_map.get(code, 400), detail={"error": {"code": code, "message": str(e)}})
    return SlotListSchema(slots=[slots_domain_to_dto(s) for s in slots])