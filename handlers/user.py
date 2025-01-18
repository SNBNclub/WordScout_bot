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


# FSM States
class AddFilterState(StatesGroup):
    waiting_for_filter = State()


class AddChatState(StatesGroup):
    waiting_for_chat = State()


# Utility function for getting or creating a user
async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str):
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalars().first()
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


# Check message against filters
async def check_message_against_filters(filters, message_text):
    if not message_text:  # Если текста нет, сразу возвращаем False
        logger.info("No text in message filter")
        return False

    for f in filters:
        if f.type == "keyword" and f.value in message_text:
            return True
        elif f.type == "exclusion" and f.value in message_text:
            return False
        elif f.type == "regex" and re.search(f.value, message_text):
            return True
    return False


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
            "/chats для настройки чатов\n"
            "/export для экспорта данных\n"
            "/status для проверки статуса."
        ),
    )


# Filters Management
@router.message(Command("filters"))
async def manage_filters(message: Message, state: FSMContext):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        filters = await session.execute(select(Filter).where(Filter.user_id == user.id))
        filter_list = filters.scalars().all()
        if filter_list:
            response = "Ваши фильтры:\n" + "\n".join(f"{f.id}. {f.type} - {f.value}" for f in filter_list)
        else:
            response = "У вас пока нет фильтров. Отправьте новый фильтр в следующем сообщении."
        await message.answer(response)
        await message.answer("Введите фильтр (например, '-исключение', 'ключевое', или 'reрегулярное выражение').")
    await state.set_state(AddFilterState.waiting_for_filter)


@router.message(AddFilterState.waiting_for_filter)
async def add_filter(message: Message, state: FSMContext):
    if message.text.startswith("-"):
        filter_type = "exclusion"
        value = message.text[1:]
    elif message.text.startswith("re"):
        filter_type = "regex"
        value = message.text[2:]
    else:
        filter_type = "keyword"
        value = message.text

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        new_filter = Filter(user_id=user.id, type=filter_type, value=value)
        session.add(new_filter)
        await session.commit()
    await message.answer("Фильтр добавлен!")
    await state.clear()


# Chats Management
@router.message(Command("chats"))
async def manage_chats(message: Message, state: FSMContext):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        chats = await session.execute(select(Chat).where(Chat.user_id == user.id))
        chat_list = chats.scalars().all()
        if chat_list:
            response = "Ваши чаты:\n" + "\n".join(f"{c.id}. {c.link}" for c in chat_list)
        else:
            response = "У вас пока нет чатов. Отправьте ссылку на новый чат в следующем сообщении."
        await message.answer(response)
    await state.set_state(AddChatState.waiting_for_chat)


@router.message(AddChatState.waiting_for_chat)
async def add_chat(message: Message, state: FSMContext):
    if message.text.startswith("https://t.me/"):
        async with async_session() as session:
            user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
            new_chat = Chat(user_id=user.id, link=message.text)
            session.add(new_chat)
            await session.commit()
        await message.answer("Чат добавлен!")
    else:
        await message.answer("Неверный формат ссылки. Пожалуйста, отправьте ссылку в формате https://t.me/название_чата")
    await state.clear()

# Status
@router.message(Command("status"))
async def get_status(message: Message):
    await message.answer("Бот работает корректно. Функции: фильтры, чаты, экспорт и статус готовы.")

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
        chat_list = chats.scalars().all()

        for chat in chat_list:
            if chat.link.endswith(message.chat.username):
                user_filters = await session.execute(
                    select(Filter).where(Filter.user_id == chat.user_id)
                )

                filters = user_filters.scalars().all()
                
                logger.info(f"Filters for user {chat.user_id}: {filters}")
                
                if await check_message_against_filters(filters, message.text):
                    user = await session.execute(
                        select(User).where(User.id == chat.user_id)
                    )
                    user = user.scalars().first()

                    await bot.send_message(
                        user.telegram_id,
                        f"Найдено сообщение в чате {message.chat.title}:\n{message.text}",
                    )

