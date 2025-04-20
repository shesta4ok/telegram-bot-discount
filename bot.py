import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiohttp import web
import asyncio

# Загружаем токен из переменных окружения
API_TOKEN = os.getenv('API_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Проверяем, что токен был загружен корректно
if API_TOKEN is None:
    logging.error("API_TOKEN не загружен!")
else:
    logging.info(f"Токен загружен: {API_TOKEN[:10]}...")  # выводим первые 10 символов токена для проверки

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    logging.info(f"Получено сообщение от {message.from_user.username}")
    await message.reply(
        "Привет! Я твой скидочный бот 🎉\nПодпишись на наш канал, и получи скидку 50% на покупку в нашем магазине! 😉",
        parse_mode=ParseMode.MARKDOWN
    )

# Обработчик callback для получения скидки
@dp.message_handler(commands=['discount'])
async def send_discount(message: types.Message):
    # Проверяем, подписан ли пользователь на канал
    user_id = message.from_user.id
    chat_id = '@bulavka_secondhand'

    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status == 'member' or member.status == 'administrator':
            await message.reply(
                "Спасибо за подписку! Ваша скидка 50%! Покажите этот код на кассе 😄🎉",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.reply(
                "Пожалуйста, подпишитесь на наш канал, чтобы получить скидку на покупки! 😅",
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        logging.error(f"Ошибка при проверке подписки: {e}")
        await message.reply("Произошла ошибка при проверке подписки. Попробуйте позже.")

# Обработчик webhook
async def handle_webhook(request):
    json_str = await request.text()
    update = types.Update.parse_raw(json_str)
    await dp.process_update(update)
    return web.Response()

# Устанавливаем webhook
async def on_start():
    logging.info("Bot started...")
    # Устанавливаем webhook на адрес
    if WEBHOOK_URL is None:
        logging.error("WEBHOOK_URL не найден! Убедитесь, что переменная окружения установлена.")
        return
    try:
        await bot.set_webhook(WEBHOOK_URL)
        logging.info(f"Webhook установлен на {WEBHOOK_URL}")
    except Exception as e:
        logging.error(f"Ошибка при установке webhook: {e}")

# Основная функция
def main():
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()

    # Запускаем webhook сервер
    app = web.Application()
    app.router.add_post(f'/{API_TOKEN}', handle_webhook)

    loop.create_task(on_start())

    # Запускаем сервер на Render
    web.run_app(app, port=10000)

if __name__ == '__main__':
    main()
