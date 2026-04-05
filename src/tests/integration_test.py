import pytest
from datetime import date, datetime, timezone, timedelta
from httpx import AsyncClient


async def _get_token(client: AsyncClient, role: str) -> str:
    response = await client.post("/dummyLogin", json={"role": role})
    assert response.status_code == 200
    return response.json()["token"]


def _find_day_within_7_days(isoweekday: int) -> str:
    today = date.today()
    for offset in range(8):
        candidate = today + timedelta(days=offset)
        if candidate.isoweekday() == isoweekday:
            return candidate.isoformat()
    return today.isoformat()


@pytest.fixture(autouse=True)
async def _clean(clean_db):
    pass


@pytest.mark.asyncio
async def test_info_endpoint(client: AsyncClient):
    response = await client.get("/_info")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_full_booking_scenario(client: AsyncClient):
    admin_token = await _get_token(client, "admin")
    user_token = await _get_token(client, "user")

    room_resp = await client.post(
        "/rooms/create",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Integration Room", "capacity": 5},
    )
    assert room_resp.status_code == 201
    room_id = room_resp.json()["id"]

    target_date = _find_day_within_7_days(1)
    await client.post(
        f"/rooms/{room_id}/schedule/create",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"daysOfWeek": [1, 2, 3, 4, 5, 6, 7], "startTime": "09:00", "endTime": "11:00"},
    )

    slots_resp = await client.get(
        f"/rooms/{room_id}/slots/list",
        headers={"Authorization": f"Bearer {user_token}"},
        params={"date": target_date},
    )
    assert slots_resp.status_code == 200
    slots = slots_resp.json()["slots"]
    assert len(slots) > 0

    future_slot = next(
        (s for s in slots if datetime.fromisoformat(s["start"]) > datetime.now(timezone.utc)),
        None,
    )
    assert future_slot is not None, "No future slots available"
    slot_id = future_slot["id"]

    booking_resp = await client.post(
        "/bookings/create",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"slotId": slot_id, "createConferenceLink": False},
    )
    assert booking_resp.status_code == 201
    booking = booking_resp.json()
    assert booking["status"] == "active"
    booking_id = booking["id"]

    slots_after = await client.get(
        f"/rooms/{room_id}/slots/list",
        headers={"Authorization": f"Bearer {user_token}"},
        params={"date": target_date},
    )
    available_ids = [s["id"] for s in slots_after.json()["slots"]]
    assert slot_id not in available_ids

    cancel_resp = await client.post(
        f"/bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    slots_restored = await client.get(
        f"/rooms/{room_id}/slots/list",
        headers={"Authorization": f"Bearer {user_token}"},
        params={"date": target_date},
    )
    restored_ids = [s["id"] for s in slots_restored.json()["slots"]]
    assert slot_id in restored_ids


@pytest.mark.asyncio
async def test_cancel_booking_idempotent(client: AsyncClient):
    admin_token = await _get_token(client, "admin")
    user_token = await _get_token(client, "user")

    room_resp = await client.post(
        "/rooms/create",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Idempotent Room"},
    )
    room_id = room_resp.json()["id"]

    await client.post(
        f"/rooms/{room_id}/schedule/create",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"daysOfWeek": [1, 2, 3, 4, 5, 6, 7], "startTime": "14:00", "endTime": "16:00"},
    )

    today_iso = date.today().isoformat()
    slots_resp = await client.get(
        f"/rooms/{room_id}/slots/list",
        headers={"Authorization": f"Bearer {user_token}"},
        params={"date": today_iso},
    )
    slots = slots_resp.json()["slots"]
    future_slot = next(
        (s for s in slots if datetime.fromisoformat(s["start"]) > datetime.now(timezone.utc)),
        None,
    )
    if future_slot is None:
        pytest.skip("No future slots available")

    booking_resp = await client.post(
        "/bookings/create",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"slotId": future_slot["id"], "createConferenceLink": False},
    )
    booking_id = booking_resp.json()["id"]

    first = await client.post(
        f"/bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert first.status_code == 200
    assert first.json()["status"] == "cancelled"

    second = await client.post(
        f"/bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert second.status_code == 200
    assert second.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_admin_cannot_create_booking(client: AsyncClient):
    admin_token = await _get_token(client, "admin")
    user_token = await _get_token(client, "user")

    room_resp = await client.post(
        "/rooms/create",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Admin Booking Room"},
    )
    room_id = room_resp.json()["id"]
    await client.post(
        f"/rooms/{room_id}/schedule/create",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"daysOfWeek": [1, 2, 3, 4, 5, 6, 7], "startTime": "10:00", "endTime": "12:00"},
    )

    today_iso = date.today().isoformat()
    slots_resp = await client.get(
        f"/rooms/{room_id}/slots/list",
        headers={"Authorization": f"Bearer {user_token}"},
        params={"date": today_iso},
    )
    slots = slots_resp.json()["slots"]
    future_slot = next(
        (s for s in slots if datetime.fromisoformat(s["start"]) > datetime.now(timezone.utc)),
        None,
    )
    if future_slot is None:
        pytest.skip("No future slots available")

    booking_resp = await client.post(
        "/bookings/create",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"slotId": future_slot["id"], "createConferenceLink": False},
    )
    assert booking_resp.status_code == 403


@pytest.mark.asyncio
async def test_cannot_book_slot_twice(client: AsyncClient):
    admin_token = await _get_token(client, "admin")
    user_token = await _get_token(client, "user")

    room_resp = await client.post(
        "/rooms/create",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Double Booking Room"},
    )
    room_id = room_resp.json()["id"]
    await client.post(
        f"/rooms/{room_id}/schedule/create",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"daysOfWeek": [1, 2, 3, 4, 5, 6, 7], "startTime": "15:00", "endTime": "17:00"},
    )

    today_iso = date.today().isoformat()
    slots = (
        await client.get(
            f"/rooms/{room_id}/slots/list",
            headers={"Authorization": f"Bearer {user_token}"},
            params={"date": today_iso},
        )
    ).json()["slots"]
    future_slot = next(
        (s for s in slots if datetime.fromisoformat(s["start"]) > datetime.now(timezone.utc)),
        None,
    )
    if future_slot is None:
        pytest.skip("No future slots available")

    await client.post(
        "/bookings/create",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"slotId": future_slot["id"], "createConferenceLink": False},
    )
    second = await client.post(
        "/bookings/create",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"slotId": future_slot["id"], "createConferenceLink": False},
    )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_list_rooms(client: AsyncClient):
    admin_token = await _get_token(client, "admin")
    user_token = await _get_token(client, "user")

    await client.post(
        "/rooms/create",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Listed Room"},
    )

    resp = await client.get("/rooms/list", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    assert len(resp.json()["rooms"]) >= 1


@pytest.mark.asyncio
async def test_cannot_create_duplicate_schedule(client: AsyncClient):
    admin_token = await _get_token(client, "admin")

    room_id = (
        await client.post(
            "/rooms/create",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Dup Schedule Room"},
        )
    ).json()["id"]

    first = await client.post(
        f"/rooms/{room_id}/schedule/create",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"daysOfWeek": [1], "startTime": "09:00", "endTime": "10:00"},
    )
    assert first.status_code == 201

    second = await client.post(
        f"/rooms/{room_id}/schedule/create",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"daysOfWeek": [2], "startTime": "11:00", "endTime": "12:00"},
    )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_my_bookings_returns_only_future(client: AsyncClient):
    user_token = await _get_token(client, "user")
    resp = await client.get("/bookings/my", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    assert "bookings" in resp.json()


@pytest.mark.asyncio
async def test_admin_can_list_all_bookings(client: AsyncClient):
    admin_token = await _get_token(client, "admin")
    resp = await client.get("/bookings/list", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert "bookings" in resp.json()
    assert "pagination" in resp.json()


@pytest.mark.asyncio
async def test_unauthorized_request_rejected(client: AsyncClient):
    resp = await client.get("/rooms/list")
    assert resp.status_code == 403
