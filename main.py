import asyncio
import logging
import time
from random import randint

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from pyrogram import Client, filters

from confige import BotConfig
from database.req import *
from handlers import errors, user, filter, chat, search
from instance import bot, app
from database.models import async_main


def register_routers(dp: Dispatcher) -> None:
    dp.include_routers(errors.router, user.router, filter.router, chat.router, search.router)


async def main() -> None:
    await async_main()

    config = BotConfig(
        admin_ids=[],
        welcome_message=""
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp["config"] = config

    register_routers(dp)

    try:
        await app.start()
        await app.send_message("me", "Hi!")
        await dp.start_polling(bot, skip_updates=True)
    except Exception as _ex:
        print(f'Exception: {_ex}')
    finally:
        await app.stop()


if __name__ == '__main__':
    asyncio.run(main())



# Регистрация обработчиков
# def register_handlers():
#     bot.add_handler(errors.handler)
#     bot.add_handler(user.handler)
#     bot.add_handler(filter.handler)
#     bot.add_handler(chat.handler)
#     bot.add_handler(search.handler)

# async def main():
    # config = BotConfig(
    #     admin_ids=[],
    #     welcome_message=""
    # )

    # await async_main()  # Инициализация БД
    # register_handlers()
    # print("Бот запущен")

    # bot = Client("my_account")
    # async with bot:
    #     await bot.send_message("me", "Hi!")

# @bot.on_message(filters.command("start"))
# async def start_command(client, message):
#     await message.reply_text("Бот запущен!")

# @bot.on_message(filters.private)
# async def hello(client, message):
#     await message.reply("Hello from Pyrogram!")


# if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO)
# asyncio.run(main())
