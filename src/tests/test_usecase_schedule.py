import pytest
from unittest.mock import AsyncMock
from uuid import UUID

from src.application.use_case.schedule import CreateScheduleUseCase
from src.core.domain.models import Room, Schedule


ROOM_ID = UUID("22222222-2222-2222-2222-222222222222")
SCHEDULE_ID = UUID("55555555-5555-5555-5555-555555555555")


def _make_room() -> Room:
    return Room(id=ROOM_ID, name="Test Room", description=None, capacity=10, created_at=None)


def _make_schedule() -> Schedule:
    return Schedule(
        id=SCHEDULE_ID,
        room_id=ROOM_ID,
        days_of_week=[1, 2, 3],
        start_time="09:00",
        end_time="18:00",
    )


@pytest.mark.asyncio
async def test_create_schedule_success():
    mock_room_repo = AsyncMock()
    mock_schedule_repo = AsyncMock()
    mock_room_repo.get_by_id.return_value = _make_room()
    mock_schedule_repo.get_by_room_id.return_value = None
    mock_schedule_repo.create.return_value = _make_schedule()

    use_case = CreateScheduleUseCase(mock_room_repo, mock_schedule_repo)
    result = await use_case.execute(ROOM_ID, [1, 2, 3], "09:00", "18:00")

    mock_schedule_repo.create.assert_called_once()
    assert result.room_id == ROOM_ID


@pytest.mark.asyncio
async def test_create_schedule_room_not_found():
    mock_room_repo = AsyncMock()
    mock_schedule_repo = AsyncMock()
    mock_room_repo.get_by_id.return_value = None

    use_case = CreateScheduleUseCase(mock_room_repo, mock_schedule_repo)
    with pytest.raises(ValueError, match="ROOM_NOT_FOUND"):
        await use_case.execute(ROOM_ID, [1], "09:00", "18:00")


@pytest.mark.asyncio
async def test_create_schedule_already_exists():
    mock_room_repo = AsyncMock()
    mock_schedule_repo = AsyncMock()
    mock_room_repo.get_by_id.return_value = _make_room()
    mock_schedule_repo.get_by_room_id.return_value = _make_schedule()

    use_case = CreateScheduleUseCase(mock_room_repo, mock_schedule_repo)
    with pytest.raises(ValueError, match="SCHEDULE_EXISTS"):
        await use_case.execute(ROOM_ID, [1], "09:00", "18:00")


@pytest.mark.asyncio
async def test_create_schedule_start_after_end():
    mock_room_repo = AsyncMock()
    mock_schedule_repo = AsyncMock()
    mock_room_repo.get_by_id.return_value = _make_room()
    mock_schedule_repo.get_by_room_id.return_value = None

    use_case = CreateScheduleUseCase(mock_room_repo, mock_schedule_repo)
    with pytest.raises(ValueError, match="INVALID_REQUEST"):
        await use_case.execute(ROOM_ID, [1], "18:00", "09:00")


@pytest.mark.asyncio
async def test_create_schedule_range_less_than_30_minutes():
    mock_room_repo = AsyncMock()
    mock_schedule_repo = AsyncMock()
    mock_room_repo.get_by_id.return_value = _make_room()
    mock_schedule_repo.get_by_room_id.return_value = None

    use_case = CreateScheduleUseCase(mock_room_repo, mock_schedule_repo)
    with pytest.raises(ValueError, match="INVALID_REQUEST"):
        await use_case.execute(ROOM_ID, [1], "09:00", "09:20")


@pytest.mark.asyncio
async def test_create_schedule_equal_start_end():
    mock_room_repo = AsyncMock()
    mock_schedule_repo = AsyncMock()
    mock_room_repo.get_by_id.return_value = _make_room()
    mock_schedule_repo.get_by_room_id.return_value = None

    use_case = CreateScheduleUseCase(mock_room_repo, mock_schedule_repo)
    with pytest.raises(ValueError, match="INVALID_REQUEST"):
        await use_case.execute(ROOM_ID, [1], "09:00", "09:00")
