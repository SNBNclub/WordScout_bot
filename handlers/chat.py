from aiogram.filters import Command, CommandStart
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from handlers.errors import safe_send_message
from keyboards.chat_kb import get_add_chat_ikb
from instance import bot
from database.req import *
from database.models import User, Filter, Chat, LikedMessage, async_session

import re

router = Router()
router.message.filter(
    F.chat.type == "private"
)

class AddChatState(StatesGroup):
    waiting_for_chat = State()

# Chats Management
@router.message(Command("chats"))
async def manage_chats(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        chats = await session.execute(select(Chat).where(Chat.user_id == user.id))
        chat_list = chats.scalars().all()
        if chat_list:
            response = "Ваши чаты:\n" + "\n".join(f"{c.link}" for c in chat_list) + "\nНажмите /add_chat, чтобы добавить ещё."
        else:
            response = "У вас пока нет чатов. Нажмите /add_chat, чтобы добавить чат."
        await message.answer(response)

@router.message(Command("add_chat"))
async def add_chat(message: Message, state: FSMContext):
    msg = await message.answer(
        text="Отправьте ссылку на чат в формате https://t.me/название_чата",
        reply_markup=get_add_chat_ikb(),
        )
    await state.update_data(message_id=msg.message_id)
    await state.set_state(AddChatState.waiting_for_chat)

@router.callback_query(F.data == "cancel_add_chat")
async def cancel_add_chat(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Отмена добавления чата.")
    await state.clear()

@router.message(AddChatState.waiting_for_chat)
async def add_chat(message: Message, state: FSMContext):
    message_text = message.text
    if message_text.startswith("@"):
        message_text = message.text.replace("@", "https://t.me/")
    if message_text.startswith("https://t.me/"):
        async with async_session() as session:
            user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
            new_chat = Chat(user_id=user.id, link=message_text)
            #no dublication
            chats = await session.execute(select(Chat).where(Chat.link == message_text).where(Chat.user_id == message.from_user.id))
            chat_list = chats.scalars().all()
            if chat_list:
                await message.answer("Чат уже существует.")
            else:
                session.add(new_chat)
                await session.commit()
                await message.answer(text=f"Чат @{message_text.split('/')[-1]} добавлен.")
    else:
        await message.answer("Неверный формат ссылки. Попробуйте ещё раз, нажав /add_chat")

    await message.delete()
    data = await state.get_data()
    message_id = data.get("message_id")
    if message_id:
        await bot.delete_message(message.chat.id, message_id)
    await state.clear()
