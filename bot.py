from dotenv import load_dotenv
import os

# Загрузка переменных окружения из .env
load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')
PORT = int(os.getenv('PORT', 5000))
WEBHOOK_HOST = os.getenv('RENDER_EXTERNAL_URL', f'https://telegram-bot-discount-1.onrender.com')
WEBHOOK_PATH = f'/{API_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
import sqlite3
from datetime import datetime
import logging
from aiohttp import web

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# База данных
def init_db():
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        received_discount BOOLEAN DEFAULT 0,
                        subscription_time TEXT
                    )''')
    conn.commit()
    conn.close()

async def check_if_received_discount(user_id):
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT received_discount FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1

def mark_discount_given(user_id):
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, received_discount, subscription_time) VALUES (?, ?, ?)",
                   (user_id, 1, datetime.now().isoformat()))
    conn.commit()
    conn.close()

async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member('@bulavka_secondhand', user_id)
        return member.status in ['member', 'creator', 'administrator']
    except Exception:
        return False

# Обработчики команд
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id

    if await check_if_received_discount(user_id):
        await message.reply("Вы уже получили свою скидку! 😎")
        return

    if await is_subscribed(user_id):
        mark_discount_given(user_id)
        await message.reply("Спасибо за подписку! 🎉 Ваша скидка 50%! Покажите на кассе! 😎")
    else:
        await message.reply(
            "Привет! 🎉\nПодпишитесь на наш канал @bulavka_secondhand и получите скидку 50%! 👉",
            reply_markup=types.ReplyKeyboardMarkup(
                resize_keyboard=True,
                one_time_keyboard=True
            ).add(
                types.KeyboardButton("Перейти на канал")
            )
        )

@dp.message_handler(lambda message: message.text == "Перейти на канал")
async def redirect_to_channel(message: types.Message):
    await message.reply("Вот ссылка на наш канал: @bulavka_secondhand",
                        reply_markup=types.ReplyKeyboardRemove())

# Webhook хендлеры
async def on_startup(app):
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()

# Запуск
if __name__ == '__main__':
    init_db()

    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, dp.process_update)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, port=PORT)
