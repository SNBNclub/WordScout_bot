from aiogram.filters import Command, CommandStart
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from handlers.errors import safe_send_message
from keyboards.keyboards import get_some_kb, get_some_ikb
from instance import bot
from database.req import *
from database.models import User, Filter, Chat, LikedMessage, async_session

import re

router = Router()
router.message.filter(
    F.chat.type == "private"
)

# /start Command
@router.message(CommandStart())
async def cmd_start(message: Message):
    async with async_session() as session:
        await get_or_create_user(session, message.from_user.id, message.from_user.username)
    await safe_send_message(
        bot,
        message,
        text=(
            "Добро пожаловать!\n"
            "Используйте /filters для настройки фильтров\n"
            "/add_filter для добавления фильтра\n"
            "/chats для настройки чатов\n"
            "/add_chat для добавления чата\n"
            "/profile для просмотра профиля\n"
        ),
    )

# Profile
@router.message(Command("profile"))
async def profile(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        filters = await session.execute(select(Filter).where(Filter.user_id == user.id))
        filter_list = filters.scalars().all()
        chats = await session.execute(select(Chat).where(Chat.user_id == user.id))
        chat_list = chats.scalars().all()
        response = (
            f"Ваш профиль:\n"
            f"ID: {user.id}\n"
            f"Telegram ID: {user.telegram_id}\n"
            f"Имя пользователя: {user.username}\n"
            f"Фильтры: {len(filter_list)}\n"
            f"Чаты: {len(chat_list)}\n"
        )
        await message.answer(response)
