import logging

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from services.db_service import get_or_create_user
from utils.keyboards import (
    main_menu_keyboard,
    report_period_keyboard,
    tax_period_keyboard,
)

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    await message.answer(
        f"🤖 *HisoblBot — AI Buxgalteringiz!*\n\n"
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        f"Men sizning shaxsiy AI buxgalteringizman. Quyidagi imkoniyatlardan foydalaning:\n\n"
        f"📥 */kirim* — Daromad qo'shish\n"
        f"📤 */chiqim* — Xarajat qo'shish\n"
        f"📊 */hisobot* — Hisobot olish (PDF)\n"
        f"🏛 */solik* — Soliq hisobi va maslahat\n\n"
        f"💡 *Misol:* `/kirim 500000 non sotdim`\n"
        f"Bot avtomatik ravishda summani, mahsulotni va kategoriyani aniqlaydi!",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 *HisoblBot Yordam*\n\n"
        "*Buyruqlar:*\n"
        "• `/kirim [summa] [tavsif]` — Daromad kiritish\n"
        "• `/chiqim [summa] [tavsif]` — Xarajat kiritish\n"
        "• `/hisobot` — Moliyaviy hisobot\n"
        "• `/solik` — Soliq maslahat\n\n"
        "*Misollar:*\n"
        "• `/kirim 500000 non sotdim`\n"
        "• `/chiqim 1000000 benzin oldim`\n"
        "• `/kirim 5 mln tovar sotdim`\n"
        "• `/chiqim 200000 kommunal to'ladim`\n\n"
        "Bot AI yordamida matnni tahlil qiladi va\n"
        "summa, mahsulot, kategoriyani aniqlaydi.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("hisobot"))
async def cmd_hisobot(message: Message):
    await message.answer(
        "📊 *Qaysi davr uchun hisobot kerak?*",
        reply_markup=report_period_keyboard(),
        parse_mode="Markdown",
    )


@router.message(Command("solik"))
async def cmd_solik(message: Message):
    await message.answer(
        "🏛 *Qaysi davr uchun soliq hisobini ko'rmoqchisiz?*",
        reply_markup=tax_period_keyboard(),
        parse_mode="Markdown",
    )
