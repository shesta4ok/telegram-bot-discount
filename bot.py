import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiohttp import web
import os

API_TOKEN = os.getenv('TELEGRAM_TOKEN')  # Ваш токен
CHANNEL_USERNAME = '@bulavka_secondhand'  # Ваш канал

# Устанавливаем логирование
logging.basicConfig(level=logging.INFO)

# Создаем экземпляры бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Сохранение подписок
subscribed_users = set()  # Хранение ID пользователей, которые подписались на канал

# Установка webhook
async def on_startup(app):
    webhook_url = f"https://{os.getenv('RENDER_URL')}/webhook/{API_TOKEN}"
    await bot.set_webhook(webhook_url)
    logging.info(f"Webhook set to {webhook_url}")

async def on_shutdown(app):
    await bot.delete_webhook()

# Обработка webhook запросов
async def handle_webhook(request):
    if request.match_info.get('token') != API_TOKEN:
        return web.Response(status=403)

    data = await request.json()
    update = types.Update(**data)
    await dp.process_update(update)
    return web.Response(status=200)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    if user_id not in subscribed_users:
        await message.reply(
            "Привет! Подпишитесь на наш канал @bulavka_secondhand и получите скидку 50%! 🎉",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.reply("Вы уже подписаны на канал, спасибо! 🎉")

# Проверка подписки на канал
@dp.message_handler(commands=['check_subscription'])
async def check_subscription(message: types.Message):
    user_id = message.from_user.id
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            if user_id not in subscribed_users:
                subscribed_users.add(user_id)
                await message.reply("Спасибо за подписку! Ваша скидка 50%! Покажите на кассе! 🎉🎉🎉")
            else:
                await message.reply("Вы уже получили скидку 50%! 🎉")
        else:
            await message.reply("Вы не подписаны на канал. Пожалуйста, подпишитесь на @bulavka_secondhand и попробуйте снова. 📲")
    except Exception as e:
        await message.reply("Произошла ошибка при проверке подписки. Попробуйте позже.")
        logging.error(f"Error checking subscription: {e}")

# Запуск webhook сервера
app = web.Application()
app.router.add_post(f'/webhook/{API_TOKEN}', handle_webhook)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# Запуск сервера
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
    web.run_app(app, port=10000)
