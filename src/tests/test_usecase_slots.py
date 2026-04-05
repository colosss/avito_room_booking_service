import pytest
from unittest.mock import AsyncMock, patch
from uuid import UUID
from datetime import date, datetime, timezone

from src.application.use_case.slots import generate_slots_for_date, GetAvailableSlotsUseCase, SLOTS_CACHE_TTL
from src.core.domain.models import Schedule, Slot, Room


ROOM_ID = UUID("22222222-2222-2222-2222-222222222222")


def _make_schedule(days_of_week: list, start_time: str, end_time: str) -> Schedule:
    return Schedule(
        id=UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
        room_id=ROOM_ID,
        days_of_week=days_of_week,
        start_time=start_time,
        end_time=end_time,
    )


def test_generate_slots_correct_count():
    monday = date(2025, 1, 6)
    schedule = _make_schedule([1], "09:00", "11:00")
    slots = generate_slots_for_date(schedule, monday)
    assert len(slots) == 4


def test_generate_slots_wrong_day_returns_empty():
    tuesday = date(2025, 1, 7)
    schedule = _make_schedule([1], "09:00", "11:00")
    slots = generate_slots_for_date(schedule, tuesday)
    assert slots == []


def test_generate_slots_30_min_duration():
    monday = date(2025, 1, 6)
    schedule = _make_schedule([1], "09:00", "10:00")
    slots = generate_slots_for_date(schedule, monday)
    assert len(slots) == 2
    for slot in slots:
        delta = slot.end - slot.start
        assert delta.total_seconds() == 1800


def test_generate_slots_start_time():
    monday = date(2025, 1, 6)
    schedule = _make_schedule([1], "10:30", "12:00")
    slots = generate_slots_for_date(schedule, monday)
    assert slots[0].start == datetime(2025, 1, 6, 10, 30, tzinfo=timezone.utc)


def test_generate_slots_are_sequential():
    monday = date(2025, 1, 6)
    schedule = _make_schedule([1], "09:00", "10:30")
    slots = generate_slots_for_date(schedule, monday)
    for i in range(1, len(slots)):
        assert slots[i].start == slots[i - 1].end


def test_generate_slots_have_stable_uuids():
    monday = date(2025, 1, 6)
    schedule = _make_schedule([1], "09:00", "10:00")
    slots_a = generate_slots_for_date(schedule, monday)
    slots_b = generate_slots_for_date(schedule, monday)
    assert [s.id for s in slots_a] == [s.id for s in slots_b]


def test_generate_slots_multiple_days():
    schedule = _make_schedule([1, 3, 5], "09:00", "10:00")
    monday = date(2025, 1, 6)
    wednesday = date(2025, 1, 8)
    tuesday = date(2025, 1, 7)
    assert len(generate_slots_for_date(schedule, monday)) == 2
    assert len(generate_slots_for_date(schedule, wednesday)) == 2
    assert len(generate_slots_for_date(schedule, tuesday)) == 0


@pytest.mark.asyncio
async def test_get_available_slots_room_not_found():
    mock_room_repo = AsyncMock()
    mock_schedule_repo = AsyncMock()
    mock_slot_repo = AsyncMock()
    mock_room_repo.get_by_id.return_value = None

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    class _FakeLock:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False

    mock_redis.lock = lambda *a, **kw: _FakeLock()

    with patch("src.application.use_case.slots.get_redis", AsyncMock(return_value=mock_redis)):
        use_case = GetAvailableSlotsUseCase(mock_room_repo, mock_schedule_repo, mock_slot_repo)
        with pytest.raises(ValueError, match="ROOM_NOT_FOUND"):
            await use_case.execute(ROOM_ID, date(2025, 1, 6))


@pytest.mark.asyncio
async def test_get_available_slots_no_schedule_returns_empty():
    mock_room_repo = AsyncMock()
    mock_schedule_repo = AsyncMock()
    mock_slot_repo = AsyncMock()
    mock_room_repo.get_by_id.return_value = Room(
        id=ROOM_ID, name="RoomA", description=None, capacity=None, created_at=None
    )
    mock_schedule_repo.get_by_room_id.return_value = None

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    class _FakeLock:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False

    mock_redis.lock = lambda *a, **kw: _FakeLock()

    with patch("src.application.use_case.slots.get_redis", AsyncMock(return_value=mock_redis)):
        use_case = GetAvailableSlotsUseCase(mock_room_repo, mock_schedule_repo, mock_slot_repo)
        result = await use_case.execute(ROOM_ID, date(2025, 1, 6))

    assert result == []
