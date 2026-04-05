from locust import HttpUser, task, between
import random
from datetime import date, timedelta


class BaseUser(HttpUser):
    abstract = True
    wait_time = between(1, 3)
    role = "user"
    rooms_cache = []

    def on_start(self):
        res = self.client.post("/dummyLogin", json={"role": self.role})

        if res.status_code != 200:
            raise Exception("Login failed")

        data = res.json()
        self.token = data.get("token")

        if not self.token:
            raise Exception("Token missing")

        self.headers = {
            "Authorization": f"Bearer {self.token}"
        }

        # загрузка комнат один раз
        if not BaseUser.rooms_cache:
            res = self.client.get("/rooms/list", headers=self.headers)
            if res.status_code == 200:
                BaseUser.rooms_cache = res.json().get("rooms", [])


class ReadOnlyUser(BaseUser):
    weight = 70

    @task(1)
    def rooms_list(self):
        self.client.get("/rooms/list", headers=self.headers)

    @task(3)
    def room_slots(self):
        if not BaseUser.rooms_cache:
            return

        room = random.choice(BaseUser.rooms_cache)
        room_id = room.get("id")

        target_date = date.today() + timedelta(days=random.randint(0, 7))

        self.client.get(
            f"/rooms/{room_id}/slots/list",
            params={"date": target_date.isoformat()},
            headers=self.headers,
            name="/rooms/[id]/slots/list"
        )


class BookingUser(BaseUser):
    weight = 20

    @task
    def my_bookings(self):
        self.client.get("/bookings/my", headers=self.headers)


class AdminUser(BaseUser):
    weight = 10
    role = "admin"

    @task(2)
    def rooms_list(self):
        self.client.get("/rooms/list", headers=self.headers)

    @task(1)
    def bookings_list(self):
        self.client.get("/bookings/list", headers=self.headers)