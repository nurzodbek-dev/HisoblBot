import io
import logging

from aiogram import Router, F
from aiogram.types import BufferedInputFile, CallbackQuery

from services.db_service import get_summary, get_transactions, get_or_create_user
from services.pdf_generator import generate_report_bytes
from utils.keyboards import main_menu_keyboard, report_period_keyboard

logger = logging.getLogger(__name__)
router = Router()

PERIOD_MAP = {
    "report_weekly": (7, "Haftalik"),
    "report_monthly": (30, "Oylik"),
    "report_yearly": (365, "Yillik"),
}


@router.callback_query(F.data == "cmd_hisobot")
async def inline_hisobot(callback: CallbackQuery):
    await callback.message.edit_text(
        "📊 *Qaysi davr uchun hisobot kerak?*",
        reply_markup=report_period_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.in_({"report_weekly", "report_monthly", "report_yearly"}))
async def generate_report(callback: CallbackQuery):
    days, label = PERIOD_MAP[callback.data]
    telegram_id = callback.from_user.id

    await callback.message.edit_text(f"📊 {label} hisobot tayyorlanmoqda...")

    user = await get_or_create_user(telegram_id=telegram_id)
    summary = await get_summary(telegram_id, days=days)
    transactions = await get_transactions(telegram_id, days=days)

    if summary["transaction_count"] == 0:
        await callback.message.edit_text(
            f"📊 {label} davr uchun tranzaksiya topilmadi.",
            reply_markup=main_menu_keyboard(),
        )
        return

    pdf_bytes = generate_report_bytes(
        summary=summary,
        transactions=transactions,
        period_label=label,
        business_name=user.business_name,
    )

    # Send text summary
    text_summary = (
        f"📊 *{label} hisobot*\n\n"
        f"💰 Jami daromad: {summary['total_income']:,.0f} UZS\n"
        f"💸 Jami xarajat: {summary['total_expense']:,.0f} UZS\n"
        f"📈 Sof foyda: {summary['net_profit']:,.0f} UZS\n"
        f"📋 Tranzaksiyalar: {summary['transaction_count']}\n"
    )
    await callback.message.answer(text_summary, parse_mode="Markdown")

    # Send PDF
    doc = BufferedInputFile(pdf_bytes, filename=f"hisobot_{label.lower()}.pdf")
    await callback.message.answer_document(
        doc,
        caption=f"📄 {label} hisobot — HisoblBot",
        reply_markup=main_menu_keyboard(),
    )
