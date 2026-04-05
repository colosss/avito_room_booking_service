import pytest
from pydantic import ValidationError
from src.application.dto.schedule import ScheduleCreateDTO


def test_valid_schedule_create_dto():
    with pytest.raises(ValidationError):
        ScheduleCreateDTO(
            daysOfWeek=[1, 2, 3],
            startTime="invalid_time",
            endTime="12:00"
        )


def test_invalid_days_of_week_empty():
    with pytest.raises(ValidationError, match="daysOfWeek must contain values from 1 to 7"):
        ScheduleCreateDTO(daysOfWeek=[], startTime="09:00", endTime="17:30")


def test_invalid_days_of_week_out_of_range():
    with pytest.raises(ValidationError, match="daysOfWeek must contain values from 1 to 7"):
        ScheduleCreateDTO(daysOfWeek=[0, 8], startTime="09:00", endTime="17:30")


def test_invalid_start_time_format():
    with pytest.raises(ValidationError, match="time must be in HH:MM format"):
        ScheduleCreateDTO(daysOfWeek=[1], startTime="9:00", endTime="17:30")


def test_invalid_end_time_format():
    with pytest.raises(ValidationError, match="time must be in HH:MM format"):
        ScheduleCreateDTO(daysOfWeek=[1], startTime="09:00", endTime="17:3")


def test_all_days_of_week_valid():
    dto = ScheduleCreateDTO(daysOfWeek=[1, 2, 3, 4, 5, 6, 7], startTime="08:00", endTime="18:00")
    assert len(dto.daysOfWeek) == 7


def test_boundary_times():
    dto = ScheduleCreateDTO(daysOfWeek=[5], startTime="00:00", endTime="23:59")
    assert dto.startTime == "00:00"
    assert dto.endTime == "23:59"
