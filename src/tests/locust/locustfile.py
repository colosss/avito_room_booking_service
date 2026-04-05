"""
Нагрузочное тестирование сервиса бронирования переговорок.
Запуск: locust -f locustfile.py --host=http://localhost:8080

Требования из задания:
  - RPS: 100
  - SLI успешности: 99.9%
  - SLI времени ответа для /slots/list: 200 мс
"""

import random
from datetime import date, timedelta
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# ─── Глобальное состояние (заполняется в on_start) ───────────────────────────

ADMIN_TOKEN = None
USER_TOKEN = None
ROOM_IDS = []       # UUID переговорок
SLOT_IDS = []       # UUID доступных слотов (для быстрого бронирования)
BOOKING_IDS = []    # UUID активных броней (для отмены)


# ─── Вспомогательные функции ──────────────────────────────────────────────────

def get_test_dates() -> list[str]:
    """Возвращает даты на ближайшие 7 дней (как в задании — 99.9% запросов)."""
    today = date.today()
    return [(today + timedelta(days=i)).isoformat() for i in range(7)]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── Сценарий: только чтение (основная нагрузка) ─────────────────────────────

class ReadOnlyUser(HttpUser):
    """
    Симулирует обычного пользователя, который просматривает переговорки и слоты.
    Самый частый сценарий — именно его оптимизирует задание (200 мс SLI).
    Соотношение: 70% всех пользователей.
    """
    weight = 70
    wait_time = between(0.5, 2)  # пауза между запросами 0.5–2 сек

    def on_start(self):
        """Получаем токены и наполняем данными при старте воркера."""
        global ADMIN_TOKEN, USER_TOKEN, ROOM_IDS

        # Получаем admin токен
        r = self.client.post("/dummyLogin", json={"role": "admin"})
        if r.status_code == 200:
            ADMIN_TOKEN = r.json()["token"]

        # Получаем user токен
        r = self.client.post("/dummyLogin", json={"role": "user"})
        if r.status_code == 200:
            USER_TOKEN = r.json()["token"]

        # Загружаем список переговорок
        if USER_TOKEN and not ROOM_IDS:
            r = self.client.get("/rooms/list", headers=auth_headers(USER_TOKEN))
            if r.status_code == 200:
                ROOM_IDS.extend([room["id"] for room in r.json().get("rooms", [])])

    @task(5)  # вес 5 — самый частый запрос (высоконагруженный эндпоинт из задания)
    def get_slots(self):
        """GET /rooms/{roomId}/slots/list — главный эндпоинт, SLI 200 мс."""
        if not ROOM_IDS or not USER_TOKEN:
            return

        room_id = random.choice(ROOM_IDS)
        test_date = random.choice(get_test_dates())

        with self.client.get(
            f"/rooms/{room_id}/slots/list",
            params={"date": test_date},
            headers=auth_headers(USER_TOKEN),
            name="/rooms/{roomId}/slots/list",  # группировка в отчёте
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                slots = response.json().get("slots", [])
                # Сохраняем слоты для других сценариев
                global SLOT_IDS
                for slot in slots[:3]:  # берём не все, чтобы не переполнить
                    if slot["id"] not in SLOT_IDS:
                        SLOT_IDS.append(slot["id"])
                response.success()
            elif response.status_code == 404:
                # Комната без расписания — это нормально
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def list_rooms(self):
        """GET /rooms/list."""
        if not USER_TOKEN:
            return
        self.client.get(
            "/rooms/list",
            headers=auth_headers(USER_TOKEN),
            name="/rooms/list",
        )

    @task(1)
    def health_check(self):
        """GET /_info — должен всегда отвечать 200."""
        self.client.get("/_info", name="/_info")


# ─── Сценарий: бронирование (смешанная нагрузка) ─────────────────────────────

class BookingUser(HttpUser):
    """
    Симулирует пользователя, который создаёт и отменяет брони.
    Соотношение: 20% всех пользователей.
    """
    weight = 20
    wait_time = between(1, 4)

    def on_start(self):
        global USER_TOKEN, ROOM_IDS
        r = self.client.post("/dummyLogin", json={"role": "user"})
        if r.status_code == 200:
            USER_TOKEN = r.json()["token"]

        if USER_TOKEN and not ROOM_IDS:
            r = self.client.get("/rooms/list", headers=auth_headers(USER_TOKEN))
            if r.status_code == 200:
                ROOM_IDS.extend([room["id"] for room in r.json().get("rooms", [])])

    @task(3)
    def create_booking(self):
        """POST /bookings/create."""
        if not SLOT_IDS or not USER_TOKEN:
            return

        slot_id = random.choice(SLOT_IDS)

        with self.client.post(
            "/bookings/create",
            json={"slotId": slot_id, "createConferenceLink": False},
            headers=auth_headers(USER_TOKEN),
            name="/bookings/create",
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                booking_id = response.json()["booking"]["id"]
                BOOKING_IDS.append(booking_id)
                # Слот занят — убираем из доступных
                if slot_id in SLOT_IDS:
                    SLOT_IDS.remove(slot_id)
                response.success()
            elif response.status_code in (409, 400):
                # 409 = уже забронирован, 400 = слот в прошлом — ожидаемо
                response.success()
            else:
                response.failure(f"Unexpected: {response.status_code} {response.text}")

    @task(2)
    def my_bookings(self):
        """GET /bookings/my."""
        if not USER_TOKEN:
            return
        self.client.get(
            "/bookings/my",
            headers=auth_headers(USER_TOKEN),
            name="/bookings/my",
        )

    @task(1)
    def cancel_booking(self):
        """POST /bookings/{bookingId}/cancel."""
        if not BOOKING_IDS or not USER_TOKEN:
            return

        booking_id = random.choice(BOOKING_IDS)

        with self.client.post(
            f"/bookings/{booking_id}/cancel",
            headers=auth_headers(USER_TOKEN),
            name="/bookings/{bookingId}/cancel",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 404):
                if booking_id in BOOKING_IDS:
                    BOOKING_IDS.remove(booking_id)
                response.success()
            else:
                response.failure(f"Unexpected: {response.status_code}")


# ─── Сценарий: администратор (редкая нагрузка) ────────────────────────────────

class AdminUser(HttpUser):
    """
    Симулирует администратора.
    Соотношение: 10% всех пользователей.
    """
    weight = 10
    wait_time = between(3, 8)

    def on_start(self):
        global ADMIN_TOKEN
        r = self.client.post("/dummyLogin", json={"role": "admin"})
        if r.status_code == 200:
            ADMIN_TOKEN = r.json()["token"]

    @task(3)
    def list_all_bookings(self):
        """GET /bookings/list (только admin, с пагинацией)."""
        if not ADMIN_TOKEN:
            return
        page = random.randint(1, 3)
        self.client.get(
            "/bookings/list",
            params={"page": page, "pageSize": 20},
            headers=auth_headers(ADMIN_TOKEN),
            name="/bookings/list",
        )

    @task(1)
    def create_room(self):
        """POST /rooms/create — редкая операция."""
        if not ADMIN_TOKEN:
            return
        with self.client.post(
            "/rooms/create",
            json={
                "name": f"Load Test Room {random.randint(1000, 9999)}",
                "description": "Created during load test",
                "capacity": random.randint(2, 20),
            },
            headers=auth_headers(ADMIN_TOKEN),
            name="/rooms/create",
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                room_id = response.json()["room"]["id"]
                if room_id not in ROOM_IDS:
                    ROOM_IDS.append(room_id)
                response.success()
            else:
                response.failure(f"Unexpected: {response.status_code}")