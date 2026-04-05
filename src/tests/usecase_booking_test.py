import pytest
import unittest
from unittest.mock import AsyncMock, patch
from uuid import UUID
from datetime import datetime, timedelta, timezone

from src.application.use_case.bookings import (
    CreateBookingUseCase,
    CancelBookingUseCase,
    GetMyBookingUseCase,
)
from src.core.domain.models import Booking, Slot
from src.infrastructure.auth.jwt import DUMMY_USER_UUID, DUMMY_ADMIN_UUID


@pytest.fixture
def mock_booking_repo():
    return AsyncMock()


@pytest.fixture
def mock_slot_repo():
    return AsyncMock()


def _make_slot(slot_id: UUID, room_id: UUID, hours_from_now: int = 1) -> Slot:
    now = datetime.now(timezone.utc)
    start = now + timedelta(hours=hours_from_now)
    return Slot(id=slot_id, room_id=room_id, start=start, end=start + timedelta(minutes=30))


def _make_booking(booking_id: UUID, slot_id: UUID, user_id: UUID, status: str = "active") -> Booking:
    return Booking(
        id=booking_id,
        slot_id=slot_id,
        user_id=user_id,
        status=status,
        conference_link=None,
        created_at=None,
    )


SLOT_ID = UUID("11111111-1111-1111-1111-111111111111")
ROOM_ID = UUID("22222222-2222-2222-2222-222222222222")
BOOKING_ID = UUID("33333333-3333-3333-3333-333333333333")
USER_ID = UUID(DUMMY_USER_UUID)
ADMIN_ID = UUID(DUMMY_ADMIN_UUID)


@pytest.mark.asyncio
async def test_create_booking_success(mock_booking_repo, mock_slot_repo):
    mock_slot_repo.get_by_id.return_value = _make_slot(SLOT_ID, ROOM_ID)
    mock_booking_repo.get_active_by_slot_id.return_value = None
    mock_booking_repo.create.return_value = _make_booking(BOOKING_ID, SLOT_ID, USER_ID)

    with patch("src.application.use_case.bookings.invalidate_slots_cache", AsyncMock()):
        use_case = CreateBookingUseCase(mock_booking_repo, mock_slot_repo)
        booking = await use_case.execute(SLOT_ID, USER_ID, create_conference_link=False)

    mock_slot_repo.get_by_id.assert_called_once_with(slot_id=SLOT_ID)
    mock_booking_repo.get_active_by_slot_id.assert_called_once_with(slot_id=SLOT_ID)
    mock_booking_repo.create.assert_called_once()
    assert booking.status == "active"


@pytest.mark.asyncio
async def test_create_booking_slot_not_found(mock_booking_repo, mock_slot_repo):
    mock_slot_repo.get_by_id.return_value = None

    use_case = CreateBookingUseCase(mock_booking_repo, mock_slot_repo)
    with pytest.raises(ValueError, match="SLOT_NOT_FOUND"):
        await use_case.execute(SLOT_ID, USER_ID)


@pytest.mark.asyncio
async def test_create_booking_slot_in_the_past(mock_booking_repo, mock_slot_repo):
    now = datetime.now(timezone.utc)
    past_start = now - timedelta(hours=2)
    past_slot = Slot(id=SLOT_ID, room_id=ROOM_ID, start=past_start, end=past_start + timedelta(minutes=30))
    mock_slot_repo.get_by_id.return_value = past_slot

    use_case = CreateBookingUseCase(mock_booking_repo, mock_slot_repo)
    with pytest.raises(ValueError, match="INVALID_REQUEST"):
        await use_case.execute(SLOT_ID, USER_ID)


@pytest.mark.asyncio
async def test_create_booking_slot_already_booked(mock_booking_repo, mock_slot_repo):
    mock_slot_repo.get_by_id.return_value = _make_slot(SLOT_ID, ROOM_ID)
    mock_booking_repo.get_active_by_slot_id.return_value = _make_booking(BOOKING_ID, SLOT_ID, ADMIN_ID)

    use_case = CreateBookingUseCase(mock_booking_repo, mock_slot_repo)
    with pytest.raises(ValueError, match="SLOT_ALREADY_BOOKED"):
        await use_case.execute(SLOT_ID, USER_ID)


@pytest.mark.asyncio
async def test_create_booking_with_conference_link(mock_booking_repo, mock_slot_repo):
    booking_with_link = Booking(
        id=BOOKING_ID,
        slot_id=SLOT_ID,
        user_id=USER_ID,
        status="active",
        conference_link="https://conference.exemple.com/room/some-uuid",
        created_at=None,
    )
    mock_slot_repo.get_by_id.return_value = _make_slot(SLOT_ID, ROOM_ID)
    mock_booking_repo.get_active_by_slot_id.return_value = None
    mock_booking_repo.create.return_value = booking_with_link

    with patch("src.application.use_case.bookings.invalidate_slots_cache", AsyncMock()):
        use_case = CreateBookingUseCase(mock_booking_repo, mock_slot_repo)
        booking = await use_case.execute(SLOT_ID, USER_ID, create_conference_link=True)

    assert booking.conference_link is not None
    assert "https://" in booking.conference_link


@pytest.mark.asyncio
async def test_cancel_booking_success(mock_booking_repo, mock_slot_repo):
    active_booking = _make_booking(BOOKING_ID, SLOT_ID, USER_ID, status="active")
    cancelled_booking = _make_booking(BOOKING_ID, SLOT_ID, USER_ID, status="cancelled")
    mock_booking_repo.get_by_id.return_value = active_booking
    mock_booking_repo.cancel.return_value = cancelled_booking
    mock_slot_repo.get_by_id.return_value = _make_slot(SLOT_ID, ROOM_ID)

    with patch("src.application.use_case.bookings.invalidate_slots_cache", AsyncMock()):
        use_case = CancelBookingUseCase(mock_booking_repo, mock_slot_repo)
        result = await use_case.execute(BOOKING_ID, USER_ID)

    assert result.status == "cancelled"
    mock_booking_repo.cancel.assert_called_once_with(booking_id=BOOKING_ID)


@pytest.mark.asyncio
async def test_cancel_booking_not_found(mock_booking_repo, mock_slot_repo):
    mock_booking_repo.get_by_id.return_value = None

    use_case = CancelBookingUseCase(mock_booking_repo, mock_slot_repo)
    with pytest.raises(ValueError, match="BOOKING_NOT_FOUND"):
        await use_case.execute(BOOKING_ID, USER_ID)


@pytest.mark.asyncio
async def test_cancel_booking_forbidden(mock_booking_repo, mock_slot_repo):
    other_user_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    booking_of_other = _make_booking(BOOKING_ID, SLOT_ID, other_user_id, status="active")
    mock_booking_repo.get_by_id.return_value = booking_of_other

    use_case = CancelBookingUseCase(mock_booking_repo, mock_slot_repo)
    with pytest.raises(ValueError, match="FORBIDDEN"):
        await use_case.execute(BOOKING_ID, USER_ID)


@pytest.mark.asyncio
async def test_cancel_already_cancelled_is_idempotent(mock_booking_repo, mock_slot_repo):
    already_cancelled = _make_booking(BOOKING_ID, SLOT_ID, USER_ID, status="cancelled")
    mock_booking_repo.get_by_id.return_value = already_cancelled

    use_case = CancelBookingUseCase(mock_booking_repo, mock_slot_repo)
    result = await use_case.execute(BOOKING_ID, USER_ID)

    assert result.status == "cancelled"
    mock_booking_repo.cancel.assert_not_called()


@pytest.mark.asyncio
async def test_get_my_bookings(mock_booking_repo):
    bookings = [
        _make_booking(BOOKING_ID, SLOT_ID, USER_ID),
        _make_booking(UUID("44444444-4444-4444-4444-444444444444"), SLOT_ID, USER_ID),
    ]
    mock_booking_repo.get_my_bookings.return_value = bookings

    use_case = GetMyBookingUseCase(mock_booking_repo)
    result = await use_case.execute(USER_ID)

    assert len(result) == 2
    mock_booking_repo.get_my_bookings.assert_called_once_with(USER_ID)
