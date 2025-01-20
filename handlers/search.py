from aiogram.filters import Command, CommandStart
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, LinkPreviewOptions
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from handlers.errors import safe_send_message
from handlers.filter import check_message_against_filters
from keyboards.keyboards import get_some_kb, get_some_ikb
from instance import bot
from database.req import *
from database.models import User, Filter, Chat, LikedMessage, async_session

import re

router = Router()

@router.message()
async def monitor_chats(message: types.Message):
    """Отслеживаем сообщения в чатах и уведомляем пользователя, если сообщение подходит под фильтры."""
    if message.chat.type not in ("group", "supergroup"):
        logger.info("Message not in group or supergroup")
        return

    if not message.text:
        logger.info("No text in message")
        return False
    
    logger.info(f"Message received in chat {message.chat.title}: {message.text}")

    async with async_session() as session:
        chats = await session.execute(select(Chat))
        chat_list = chats.scalars().unique().all()

        for chat in chat_list:
            if chat.link.endswith(message.chat.username):
                user_filters = await session.execute(
                    select(Filter).where(Filter.user_id == chat.user_id)
                )
                filters = user_filters.scalars().unique().all()
                
                logger.info(f"Filters for user {chat.user_id}: {filters}")
                
                if await check_message_against_filters(filters, message.text):
                    users_list = await session.execute(
                        select(User).where(User.id == chat.user_id)
                    )
                    users = users_list.scalars().unique().all()
                    for user in users:
                        await bot.send_message(
                            user.telegram_id,
                            text=f"Найдено сообщение:\n{message.text[:239]}\n\nЧат: {message.chat.title}\nАвтор: @{message.from_user.username}\nСсылка: https://t.me/{message.chat.username}/{message.message_id}",
                            link_preview_options=LinkPreviewOptions(is_disabled=True),
                        )

