from fastapi import APIRouter, Depends, HTTPException, Query
from src.interfaces.api.dependencies import require_admin, require_user
from src.infrastructure.database.db_helper import db_helper
from src.infrastructure.database.repositories.bookings import BookingRepository
from src.infrastructure.database.repositories.slots import SlotRepository
from src.application.dto.booking import (
    BookingCreateDTO,
    BookingListSchema,
    BookingSchema,
    MyBookingListSchema,
    PaginationSchema,
)
from src.application.use_case.bookings import(
    CreateBookingUseCase,
    CancelBookingUseCase,
    GetMyBookingUseCase,
    ListAllBookingUseCase,
)
from src.application.mappers.bookings import bookings_domain_to_dto
from uuid import UUID

router=APIRouter(tags=["Bookings"])

@router.post("/bookings/create", response_model=BookingSchema, status_code=201)
async def create_booking(
    body: BookingCreateDTO,
    current_user: dict=Depends(require_user),
    session=Depends(db_helper.session_dependency),
):
    try:
        booking=await CreateBookingUseCase(
            bookint_repo=BookingRepository(session=session),
            slot_repo=SlotRepository(session=session)
        ).execute(
            slot_id=body.slotId,
            user_id=UUID(current_user["user_id"]),
            create_conference_link=body.createConferenceLink
        )
    except ValueError as e:
        code = str(e).split(":")[0]
        status_map = {"SLOT_NOT_FOUND": 404, "SLOT_ALREADY_BOOKED": 409, "INVALID_REQUEST": 400}
        raise HTTPException(status_map.get(code, 400), detail={"error": {"code": code, "message": str(e)}})
    return bookings_domain_to_dto(booking)

@router.get("/bookings/my", response_model=MyBookingListSchema)
async def my_bookings(
    current_user:dict=Depends(require_user),
    session=Depends(db_helper.session_dependency)):

    bookings=await GetMyBookingUseCase(
        booking_repo=BookingRepository(session=session)
        ).execute(UUID(current_user["user_id"]))
    return MyBookingListSchema(bookings=[bookings_domain_to_dto(b) for b in bookings])


@router.get("/bookings/list", response_model=BookingListSchema)
async def list_bookings(
    page: int=Query(default=1, ge=1),
    pageSize: int=Query(default=20, ge=1, le=100),
    current_user:dict=Depends(require_admin),
    session=Depends(db_helper.session_dependency)):

    bookings, total = await ListAllBookingUseCase(
        booking_repo=BookingRepository(session=session)
        ).execute(page=page, page_size=pageSize)
    return BookingListSchema(
        bookings=[bookings_domain_to_dto(b) for b in bookings],
        pagination=PaginationSchema(page=page, pageSize=pageSize, total=total),
    )


@router.post("/bookings/{bookingId}/cancel", response_model=BookingSchema)
async def cancel_booking(
    bookingId: UUID,
    current_user: dict=Depends(require_user),
    session=Depends(db_helper.session_dependency)):

    try:
        booking=await CancelBookingUseCase(
            BookingRepository(session=session),
            slot_repo=SlotRepository(session=session)).execute(
            booking_id=bookingId, user_id=UUID(current_user["user_id"])
        )
        if booking is None:
            raise HTTPException(404, detail={"error": {"code": "BOOKING_NOT_FOUND", "message": "booking not found"}})
    except ValueError as e:
        code=str(e)
        messages = {
            "BOOKING_NOT_FOUND": "booking not found",
            "FORBIDDEN": "cannot cancel another user's booking",
        }
        status_map = {"BOOKING_NOT_FOUND": 404, "FORBIDDEN": 403}
        raise HTTPException(
            status_map.get(code, 400), 
            detail={"error": {"code": code, "message": messages.get(code, code.lower())}},
        )
    return bookings_domain_to_dto(booking)