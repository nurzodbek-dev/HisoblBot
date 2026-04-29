import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from handlers.commands import router as commands_router
from handlers.reports import router as reports_router
from handlers.settings import router as settings_router
from handlers.tax import router as tax_router
from handlers.transactions import router as transactions_router
from services.db_service import init_db
from services.scheduler import setup_scheduler
from utils.config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main():
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set!")
        sys.exit(1)

    # Initialize database
    logger.info("Initializing database...")
    await init_db()

    # Create bot and dispatcher
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers
    dp.include_router(commands_router)
    dp.include_router(transactions_router)
    dp.include_router(reports_router)
    dp.include_router(tax_router)
    dp.include_router(settings_router)

    # Setup scheduler
    sched = setup_scheduler(bot)
    sched.start()
    logger.info("Scheduler started with weekly and monthly report jobs")

    # Start polling
    logger.info("HisoblBot is starting...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        sched.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
