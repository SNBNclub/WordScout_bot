from aiogram import Bot
from aiogram.enums import ParseMode
import os
from pyrogram import Client

from dotenv import load_dotenv
import sys
from aiogram.client.bot import DefaultBotProperties
import logging
import asyncio

sys.path.append(os.path.join(sys.path[0], 'k_bot'))

load_dotenv('.env')
TOKEN_API_TG = os.getenv('TOKEN_API_TG')
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

SQL_URL_RC = os.getenv('DATABASE_URL')

# SQL_URL_RC = (f'postgresql+asyncpg://{os.getenv("DB_USER")}:{os.getenv("DB_PASS")}'
#               f'@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}')

bot = Bot(
    token=TOKEN_API_TG,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

# Create an instance of the Client class, passing your bot's API_ID and API_HASH.
# app = Client(
#     name="my_account",
#     api_id=API_ID,
#     api_hash=API_HASH,
#     bot_token=BOT_TOKEN,
#     system_lang_code='ru',
#     lang_code='ru'
# )

# Alternatively, you can create an instance of the Client class using environment variables:
app = Client("my_account")

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )


logger = logging.getLogger(__name__)
