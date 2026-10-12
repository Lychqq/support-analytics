from fastapi import Depends
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Annotated


import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/vk_support_db"
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# Обратная совместимость для старого вызова
crate_db_and_tables = create_db_and_tables

async def get_session():
    async with async_session_maker() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


