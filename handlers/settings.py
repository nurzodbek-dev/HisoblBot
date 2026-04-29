import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select, update

from models.user import User
from services.db_service import async_session, get_or_create_user
from utils.keyboards import main_menu_keyboard, settings_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "cmd_settings")
async def inline_settings(callback: CallbackQuery):
    user = await get_or_create_user(telegram_id=callback.from_user.id)
    await callback.message.edit_text(
        "⚙️ *Sozlamalar*\n\n"
        "Avtomatik hisobot yuborishni sozlang:",
        reply_markup=settings_keyboard(user.weekly_report, user.monthly_report),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "toggle_weekly")
async def toggle_weekly(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.weekly_report = not user.weekly_report
            await session.commit()
            await session.refresh(user)
            await callback.message.edit_reply_markup(
                reply_markup=settings_keyboard(user.weekly_report, user.monthly_report)
            )
    await callback.answer("Haftalik hisobot sozlamasi o'zgartirildi ✅")


@router.callback_query(F.data == "toggle_monthly")
async def toggle_monthly(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.monthly_report = not user.monthly_report
            await session.commit()
            await session.refresh(user)
            await callback.message.edit_reply_markup(
                reply_markup=settings_keyboard(user.weekly_report, user.monthly_report)
            )
    await callback.answer("Oylik hisobot sozlamasi o'zgartirildi ✅")
