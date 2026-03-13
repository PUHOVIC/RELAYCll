import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp
import logging
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in .env file")

SERVER_URL = "http://localhost:5000"  # Если сервер на другой машине, замени на http://IP:5000

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот для связи с твоим кнопочным телефоном.\n"
        "Напиши мне что-нибудь, и оно появится на телефоне.\n"
        "Когда ответят с телефона, я тебе перешлю!"
    )

@dp.message()
async def forward_to_server(message: types.Message):
    user_id = str(message.from_user.id)
    text = message.text
    
    if not text:
        await message.answer("Пожалуйста, отправь текстовое сообщение")
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SERVER_URL}/incoming",
                json={"user_id": user_id, "text": text}
            ) as resp:
                if resp.status == 200:
                    await message.answer("✅ Сообщение отправлено на телефон. Жди ответа!")
                else:
                    await message.answer("❌ Ошибка при отправке на сервер")
    except Exception as e:
        logging.error(f"Error forwarding message: {e}")
        await message.answer("❌ Не удалось связаться с сервером")

async def check_outgoing_messages():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{SERVER_URL}/get_outgoing") as resp:
                    if resp.status == 200:
                        outgoing = await resp.json()
                        for msg in outgoing:
                            user_id = msg['user_id']
                            text = msg['text']
                            try:
                                await bot.send_message(
                                    user_id,
                                    f"📞 Ответ с телефона:\n\n{text}"
                                )
                                logging.info(f"Sent reply to {user_id}")
                            except Exception as e:
                                logging.error(f"Failed to send to {user_id}: {e}")
        except Exception as e:
            logging.error(f"Error checking outgoing: {e}")
        
        await asyncio.sleep(2)

async def main():
    asyncio.create_task(check_outgoing_messages())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
