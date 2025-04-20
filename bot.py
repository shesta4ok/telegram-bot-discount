from dotenv import load_dotenv
import os

load_dotenv()  # Загружаем переменные окружения из .env
API_TOKEN = os.getenv('BOT_TOKEN')
PORT = int(os.getenv('PORT', 5000))  # PORT задается Render автоматически
WEBHOOK_HOST = f"https://telegram-bot-discount-1.onrender.com"
WEBHOOK_PATH = f"/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
import sqlite3
from datetime import datetime
import logging
from aiohttp import web

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ─────── База данных ───────
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
        return member.status == 'member'
    except Exception:
        return False

# ─────── Обработка сообщений
