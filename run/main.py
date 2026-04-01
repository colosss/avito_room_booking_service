from dotenv import load_dotenv
load_dotenv

import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.infrastructure.database.db_helper import db_helper
from src.infrastructure.database.base import Base
# from src.interfaces.api import

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)
# app.include_router(post)

if __name__ == "__main__":
    uvicorn.run("cmd.main:app", reload=True)