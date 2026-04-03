from src.core.repositories import AbstractRoomRepository
from typing import Optional

class CreateRoomUseCase:
    def __init__(self, room_repo: AbstractRoomRepository):
        self._repo=room_repo

    async def execute(self, name: str, description: Optional[str], capacity:Optional[int]):
        return await self._repo.create(name=name, description=description, capacity=capacity)
    
class ListRoomsUseCase:
    def __init__(self, room_repo: AbstractRoomRepository):
        self._repo=room_repo

    async def execute(self):
        return await self._repo.get_list()