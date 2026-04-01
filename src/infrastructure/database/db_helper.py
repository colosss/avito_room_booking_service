from asyncio import current_task
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    async_scoped_session,
)
from sqlalchemy.orm import sessionmaker
from src.infrastructure.database.db_config import settings
# from src.infrastructure.database.repositories.merch import MerchRepository


class DataBaseHelper:
    def __init__(self, url: str, echo: bool = False):
        self.engine = create_async_engine(
            url = url,
            echo = echo,
        )
        self.session_factory = async_sessionmaker(
            bind = self.engine,
            autoflush = False,
            autocommit = False,
            expire_on_commit = False,
        )
    
    def get_scope_session(self):
# from src.infrastructure.database.repositories.user import 
# from src.infrastructure.database.repositories.merch import MerchRepository
# from src.infrastructure.database.repositories.user import UserRepository
        session = async_scoped_session(
            session_factory = self.session_factory,
            scopefunc = current_task,
        )
        return session
    
    async def session_dependency(self) -> AsyncSession:
        async with self.session_factory() as session:
            yield session
            await session.close()

    async def scope_session_dependency(self) -> AsyncSession:
        session = self.get_scope_session()
        yield session
        await session.close()

    async def get_room_repo(self)->RoomRepository:
        async with self.session_factory() as session:
            yield RoomRepository(session=session)
 
db_helper = DataBaseHelper(
    url = settings.db.url,
    echo = settings.db.echo,
)