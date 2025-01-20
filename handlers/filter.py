from aiogram.filters import Command, CommandStart
from aiogram import Router, F, types, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy.future import select

from handlers.errors import safe_send_message
from keyboards.filter_kb import get_add_filter_ikb
from instance import bot
from database.req import *
from database.models import User, Filter, Chat, LikedMessage, async_session

import re

router = Router()
router.message.filter(
    F.chat.type == "private"
)

# FSM States
class AddFilterState(StatesGroup):
    waiting_for_filter = State()

# Check message against filters
async def check_message_against_filters(filters, message_text):
    if not message_text:
        return False
    message_text = message_text.lower()

    ans = False
    for f in filters:
        if f.type == "keyword" and f.value in message_text:
            ans = True
        elif f.type == "exclusion" and f.value in message_text:
            return False
        elif f.type == "regex" and re.search(f.value, message_text):
            return True
    return ans

# Filters Management
@router.message(Command("filters"))
async def manage_filters(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        filters = await session.execute(select(Filter).where(Filter.user_id == user.id))
        filter_list = filters.scalars().all()
        if filter_list:
            response = "Ваши фильтры:\n" + "\n".join(f"{f.type} - {f.value}" for f in filter_list) + "\n\nНажмите /add_filter ниже, чтобы добавить ещё."
        else:
            response = "У вас пока нет фильтров. Нажмите /add_filter ниже, чтобы добавить."
        await message.answer(response)

@router.message(Command("add_filter"))
async def add_filter(message: Message, state: FSMContext):
    msg = await message.answer(
        text="Введите фильтр, они бывают трёх типов:\n1.'ключевое слово'\n2. '-исключение' -- начинается с '-'\n3. 're:регулярное выражение' -- начинается с 're'",
        reply_markup=get_add_filter_ikb(),
        )
    await state.update_data(message_id=msg.message_id)
    await state.set_state(AddFilterState.waiting_for_filter)

@router.callback_query(F.data == "cancel_add_filter")
async def cancel_add_filter(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Отмена добавления фильтра")
    await state.clear()

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
    value = value.lower()

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        new_filter = Filter(user_id=user.id, type=filter_type, value=value)
        filters = await session.execute(select(Filter).where(Filter.user_id == user.id))
        filter_list = filters.scalars().all()
        if any(f.value == value for f in filter_list):
            await message.answer(f"Фильтр '{value}' уже существует.")
        else:
            session.add(new_filter)
            await session.commit()
            await message.answer(f"Фильтер '{value}' типа {filter_type} добавлен.")

    await message.delete()
    data = await state.get_data()
    message_id = data.get("message_id")
    if message_id:
        await bot.delete_message(message.chat.id, message_id)

    await state.clear()
