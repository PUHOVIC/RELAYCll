import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Сюда вставишь токен от @BotFather
SERVER_URL = "http://localhost:5000"  # Адрес твоего сервера

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Привет! Я бот-пересыльщик. Отправь мне сообщение и оно будет отправленно.")

@dp.message()
async def forward_to_server(message: types.Message):
    """Пересылает сообщение от пользователя на сервер"""
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
                    await message.answer("✅ Сообщение отправлено на телефон")
                else:
                    await message.answer("❌ Ошибка при отправке на сервер")
    except Exception as e:
        logging.error(f"Error forwarding message: {e}")
        await message.answer("❌ Не удалось связаться с сервером")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
