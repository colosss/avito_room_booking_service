from fastapi import APIRouter, Depends, HTTPException
from src.interfaces.api.dependencies import require_admin
from src.infrastructure.database.db_helper import db_helper
from src.infrastructure.database.repositories.schedules import ScheduleRepository
from src.infrastructure.database.repositories.rooms import RoomRepository
from src.application.use_case.schedule import CreateScheduleUseCase
from src.application.dto.schedule import ScheduleCreateDTO
from src.application.mappers.schedules import schedules_domain_to_dto
from uuid import UUID

router=APIRouter(tags=["Schedule"])

@router.post("/rooms/{roomId}/schedule/create", response_model=dict, status_code=201)
async def create_schedule(
    roomId:UUID,
    body: ScheduleCreateDTO,
    current_user: dict = Depends(require_admin),
    session=Depends(db_helper.session_dependency)):
        
    try:
        schedule=await CreateScheduleUseCase(
                RoomRepository(session=session), 
                ScheduleRepository(session=session)
                ).execute(
                        room_id=roomId,
                        days_of_week=body.daysOfWeek,
                        start_time=body.startTime,
                        end_time=body.endTime,
                )
    except ValueError as e:
        code = str(e).split(":")[0]
        status_map = {"ROOM_NOT_FOUND": 404, "SCHEDULE_EXISTS": 409}
        raise HTTPException(status_map.get(code, 400),
        detail={"error": {"code": code, "message": str(e)}})
    return {"schedule": schedules_domain_to_dto(schedule).model_dump()}