from dotenv import load_dotenv
import os

load_dotenv()  # Загружаем переменные окружения из .env файла
API_TOKEN = os.getenv('BOT_TOKEN')

import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils.executor import start_webhook
import sqlite3
from datetime import datetime
import os

API_TOKEN = os.getenv("BOT_TOKEN")  # Используем переменную окружения
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # например: https://your-app.onrender.com
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", default=8000))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


def init_db():
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            received_discount BOOLEAN DEFAULT 0,
            subscription_time TEXT
        )
    """)
    conn.commit()
    conn.close()


async def check_if_received_discount(user_id):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT received_discount FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1


def mark_discount_given(user_id):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, received_discount, subscription_time) VALUES (?, ?, ?)",
                   (user_id, 1, datetime.now().isoformat()))
    conn.commit()
    conn.close()


async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member('@bulavka_secondhand', user_id)
        return member.status in ('member', 'creator', 'administrator')
    except Exception:
        return False


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id

    if await check_if_received_discount(user_id):
        await message.reply("Вы уже получили свою скидку! 😎")
        return

    if await is_subscribed(user_id):
        mark_discount_given(user_id)
        await message.reply(
            "Спасибо за подписку! 🎉 Ваша скидка 50%! Покажите на кассе! 😎",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.reply(
            "Привет! 🎉\nПодпишитесь на наш канал @bulavka_secondhand и получите скидку 50%! 👉",
            reply_markup=types.ReplyKeyboardMarkup(
                resize_keyboard=True,
                one_time_keyboard=True
            ).add(types.KeyboardButton("Перейти на канал"))
        )


@dp.message_handler(lambda message: message.text == "Перейти на канал")
async def redirect_to_channel(message: types.Message):
    await message.reply(
        "Вот ссылка на наш канал: @bulavka_secondhand",
        reply_markup=types.ReplyKeyboardRemove()
    )


async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL)
    init_db()


async def on_shutdown(dispatcher):
    await bot.delete_webhook()


if __name__ == "__main__":
    init_db()
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
