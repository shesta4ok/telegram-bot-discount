from dotenv import load_dotenv
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
import sqlite3
from datetime import datetime
import logging
from aiohttp import web

# Загружаем переменные окружения из .env файла
load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')
PORT = int(os.getenv('PORT', 5000))  # Значение по умолчанию 5000

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Подключаемся к базе данных SQLite (или создаем её, если не существует)
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
    """Проверка, если пользователь уже получил скидку."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT received_discount FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1

def mark_discount_given(user_id):
    """Отметить, что пользователь получил скидку."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, received_discount, subscription_time) VALUES (?, ?, ?)",
                   (user_id, 1, datetime.now().isoformat()))
    conn.commit()
    conn.close()

async def is_subscribed(user_id):
    """Проверка подписки на канал."""
    try:
        member = await bot.get_chat_member('@bulavka_secondhand', user_id)
        return member.status == 'member'
    except Exception:
        return False

# Команда /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id

    # Проверяем, если скидка уже была выдана
    if await check_if_received_discount(user_id):
        await message.reply("Вы уже получили свою скидку! 😎")
        return

    # Проверка подписки
    if await is_subscribed(user_id):
        # Если подписан и еще не получил скидку
        mark_discount_given(user_id)
        await message.reply(
            "Спасибо за подписку! 🎉 Ваша скидка 50%! Покажите на кассе! 😎",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Если не подписан
        await message.reply(
            "Привет! 🎉\nПодпишитесь на наш канал @bulavka_secondhand и получите скидку 50%! 👉",
            reply_markup=types.ReplyKeyboardMarkup(
                resize_keyboard=True,
                one_time_keyboard=True
            ).add(
                types.KeyboardButton("Перейти на канал")
            )
        )

# Обработка кнопки "Перейти на канал"
@dp.message_handler(lambda message: message.text == "Перейти на канал")
async def redirect_to_channel(message: types.Message):
    await message.reply(
        "Вот ссылка на наш канал: @bulavka_secondhand",
        reply_markup=types.ReplyKeyboardRemove()
    )

# Устанавливаем webhook
async def on_startup(app):
    """Устанавливаем webhook при старте приложения"""
    webhook_url = f'https://telegram-bot-discount-1.onrender.com/{API_TOKEN}'  # Правильный URL для Render
    await bot.set_webhook(url=webhook_url)
    logging.info(f"Webhook set to {webhook_url}")

async def on_shutdown(app):
    """Удаляем webhook при остановке приложения"""
    await bot.delete_webhook()
    logging.info("Webhook deleted")

# Создаём веб-сервер
app = web.Application()

# Обработчик вебхука
app.router.add_post(f'/{API_TOKEN}', dp.process_update)

# Стартуем сервер
if __name__ == '__main__':
    logging.info(f"Starting bot on port {PORT}...")
    init_db()  # Инициализация базы данных

    # Добавляем обработчики для старта и остановки
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Запускаем веб-сервер для обработки запросов
    web.run_app(app, port=PORT)
