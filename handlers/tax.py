import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

from services.ai_parser import get_tax_advice
from services.db_service import get_summary
from utils.keyboards import main_menu_keyboard, tax_period_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "cmd_solik")
async def inline_solik(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏛 *Qaysi davr uchun soliq hisobini ko'rmoqchisiz?*",
        reply_markup=tax_period_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.in_({"tax_monthly", "tax_yearly"}))
async def calculate_tax(callback: CallbackQuery):
    days = 30 if callback.data == "tax_monthly" else 365
    label = "Oylik" if callback.data == "tax_monthly" else "Yillik"
    telegram_id = callback.from_user.id

    await callback.message.edit_text(f"🏛 {label} soliq hisobi tayyorlanmoqda...")

    summary = await get_summary(telegram_id, days=days)

    if summary["transaction_count"] == 0:
        await callback.message.edit_text(
            f"🏛 {label} davr uchun tranzaksiya topilmadi.",
            reply_markup=main_menu_keyboard(),
        )
        return

    advice = await get_tax_advice(summary)

    # Truncate if too long for Telegram
    if len(advice) > 4000:
        advice = advice[:4000] + "\n\n... (qisqartirildi)"

    await callback.message.answer(
        f"🏛 *{label} soliq hisobi va maslahat:*\n\n{advice}",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
