import asyncio
from pyrogram import Client
from instance import API_ID, API_HASH, BOT_TOKEN



# Create an instance of the Client class, passing your bot's API_ID and API_HASH.
app = Client(
    name="my_account",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    system_lang_code='ru',
    lang_code='ru'
)

# Alternatively, you can create an instance of the Client class using environment variables:
# app = Client("my_account")

async def main():
    await app.start()
    await app.send_message("me", "Hi!")
    await app.stop()

if __name__ == '__main__':
    asyncio.run(main())