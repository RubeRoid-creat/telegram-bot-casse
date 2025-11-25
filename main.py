import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import config
import database as db
import handlers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция запуска бота"""
    try:
        # Проверка токена
        if not config.BOT_TOKEN:
            logger.error("BOT_TOKEN не найден в переменных окружения")
            raise ValueError("BOT_TOKEN не найден")
        
        logger.info("Инициализация базы данных...")
        # Инициализация базы данных
        await db.init_db()
        logger.info("База данных инициализирована")
        
        # Создание бота и диспетчера
        logger.info("Создание бота и диспетчера...")
        bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dp = Dispatcher()
        
        # Регистрация роутеров
        dp.include_router(handlers.router)
        logger.info("Роутеры зарегистрированы")
        
        # Проверка подключения к Telegram API
        logger.info("Проверка подключения к Telegram API...")
        bot_info = await bot.get_me()
        logger.info(f"Бот подключен: @{bot_info.username} ({bot_info.first_name})")
        
        # Запуск бота
        logger.info("Запуск polling...")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)
        exit(1)

