from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, ARRAY, BigInteger, ForeignKey, Numeric, JSON, Date, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs

from instance import SQL_URL_RC

engine = create_async_engine(url=SQL_URL_RC, echo=True)
async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True, index=True, nullable=False)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String, default='')
    username = Column(String, nullable=True)
    is_superuser = Column(Boolean, default=False)

class Filter(Base):
    __tablename__ = 'filters'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(String, nullable=False)  # keyword, exclusion, regex
    value = Column(String, nullable=False)

class Chat(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    link = Column(String, nullable=False)

class LikedMessage(Base):
    __tablename__ = 'liked_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message_text = Column(Text, nullable=False)
    chat_link = Column(String, nullable=False)
    message_link = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
