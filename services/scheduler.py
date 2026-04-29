import asyncio
import logging

from aiogram import Bot
from aiogram.types import BufferedInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from services.db_service import get_all_subscribed_users, get_summary, get_transactions
from services.pdf_generator import generate_report_bytes
from utils.config import config
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Configure and return the scheduler with weekly/monthly report jobs."""

    # Weekly report — every Monday at configured hour
    scheduler.add_job(
        send_periodic_reports,
        "cron",
        day_of_week=config.WEEKLY_REPORT_DAY,
        hour=config.WEEKLY_REPORT_HOUR,
        minute=0,
        args=[bot, "weekly"],
        id="weekly_report",
        replace_existing=True,
    )

    # Monthly report — 1st of every month at configured hour
    scheduler.add_job(
        send_periodic_reports,
        "cron",
        day=config.MONTHLY_REPORT_DAY,
        hour=config.MONTHLY_REPORT_HOUR,
        minute=0,
        args=[bot, "monthly"],
        id="monthly_report",
        replace_existing=True,
    )

    return scheduler


async def send_periodic_reports(bot: Bot, report_type: str = "weekly"):
    """Send reports to all subscribed users."""
    days = 7 if report_type == "weekly" else 30
    label = "Haftalik" if report_type == "weekly" else "Oylik"

    users = await get_all_subscribed_users(report_type)
    logger.info(f"Sending {report_type} reports to {len(users)} users")

    for user in users:
        try:
            summary = await get_summary(user.telegram_id, days=days)
            if summary["transaction_count"] == 0:
                continue

            transactions = await get_transactions(user.telegram_id, days=days)
            pdf_bytes = generate_report_bytes(
                summary=summary,
                transactions=transactions,
                period_label=label,
                business_name=user.business_name,
            )

            text = (
                f"📊 *Avtomatik {label.lower()} hisobot*\n\n"
                f"💰 Daromad: {summary['total_income']:,.0f} UZS\n"
                f"💸 Xarajat: {summary['total_expense']:,.0f} UZS\n"
                f"📈 Foyda: {summary['net_profit']:,.0f} UZS"
            )
            await bot.send_message(
                user.telegram_id, text, parse_mode="Markdown"
            )

            doc = BufferedInputFile(pdf_bytes, filename=f"hisobot_{label.lower()}.pdf")
            await bot.send_document(
                user.telegram_id,
                doc,
                caption=f"📄 {label} hisobot — HisoblBot",
                reply_markup=main_menu_keyboard(),
            )

            await asyncio.sleep(0.5)  # Rate limiting

        except Exception as e:
            logger.error(f"Failed to send report to {user.telegram_id}: {e}")
