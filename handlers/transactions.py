import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from models.transaction import TransactionType
from services.ai_parser import parse_transaction
from services.db_service import add_transaction, get_or_create_user, get_transactions
from utils.keyboards import (
    back_keyboard,
    confirm_transaction_keyboard,
    main_menu_keyboard,
)

logger = logging.getLogger(__name__)
router = Router()


class TransactionStates(StatesGroup):
    waiting_for_income_input = State()
    waiting_for_expense_input = State()
    confirming_transaction = State()


@router.message(Command("kirim"))
async def cmd_kirim(message: Message, state: FSMContext):
    await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )

    text = message.text.replace("/kirim", "").strip()
    if text:
        await _process_transaction(message, state, text, TransactionType.INCOME)
    else:
        await state.set_state(TransactionStates.waiting_for_income_input)
        await message.answer(
            "📥 *Daromad kiritish*\n\n"
            "Summani va tavsifni yozing.\n"
            "Misol: `500000 non sotdim`",
            parse_mode="Markdown",
            reply_markup=back_keyboard(),
        )


@router.message(Command("chiqim"))
async def cmd_chiqim(message: Message, state: FSMContext):
    await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )

    text = message.text.replace("/chiqim", "").strip()
    if text:
        await _process_transaction(message, state, text, TransactionType.EXPENSE)
    else:
        await state.set_state(TransactionStates.waiting_for_expense_input)
        await message.answer(
            "📤 *Xarajat kiritish*\n\n"
            "Summani va tavsifni yozing.\n"
            "Misol: `1000000 benzin oldim`",
            parse_mode="Markdown",
            reply_markup=back_keyboard(),
        )


@router.message(TransactionStates.waiting_for_income_input)
async def process_income_input(message: Message, state: FSMContext):
    await _process_transaction(message, state, message.text, TransactionType.INCOME)


@router.message(TransactionStates.waiting_for_expense_input)
async def process_expense_input(message: Message, state: FSMContext):
    await _process_transaction(message, state, message.text, TransactionType.EXPENSE)


async def _process_transaction(
    message: Message,
    state: FSMContext,
    text: str,
    tx_type: TransactionType,
):
    """Parse and confirm a transaction."""
    await message.answer("🔄 Tahlil qilinmoqda...")

    parsed = await parse_transaction(text)
    if not parsed or not parsed.get("amount"):
        await message.answer(
            "❌ Matnni tushunib bo'lmadi. Iltimos, qaytadan urinib ko'ring.\n"
            "Misol: `500000 non sotdim`",
            parse_mode="Markdown",
            reply_markup=back_keyboard(),
        )
        await state.clear()
        return

    type_label = "📥 Kirim" if tx_type == TransactionType.INCOME else "📤 Chiqim"
    await state.update_data(
        parsed=parsed,
        tx_type=tx_type.value,
        raw_input=text,
    )
    await state.set_state(TransactionStates.confirming_transaction)

    await message.answer(
        f"{type_label} — *Tasdiqlash*\n\n"
        f"💰 Summa: *{parsed['amount']:,.0f} {parsed.get('currency', 'UZS')}*\n"
        f"📦 Mahsulot: {parsed.get('item', 'N/A')}\n"
        f"📂 Kategoriya: {parsed.get('category', 'N/A')}\n"
        f"📝 Tavsif: {parsed.get('description', 'N/A')}\n",
        parse_mode="Markdown",
        reply_markup=confirm_transaction_keyboard(tx_type.value),
    )


@router.callback_query(F.data.startswith("confirm_"))
async def confirm_transaction(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("parsed"):
        await callback.answer("Ma'lumot topilmadi, qaytadan urinib ko'ring.", show_alert=True)
        await state.clear()
        return

    parsed = data["parsed"]
    tx_type = TransactionType(data["tx_type"])

    tx = await add_transaction(
        telegram_id=callback.from_user.id,
        tx_type=tx_type,
        amount=parsed["amount"],
        item=parsed.get("item"),
        category=parsed.get("category"),
        description=parsed.get("description"),
        raw_input=data.get("raw_input"),
    )

    type_emoji = "📥" if tx_type == TransactionType.INCOME else "📤"
    await callback.message.edit_text(
        f"{type_emoji} *Tranzaksiya saqlandi!*\n\n"
        f"💰 Summa: {parsed['amount']:,.0f} {parsed.get('currency', 'UZS')}\n"
        f"📦 {parsed.get('item', '')}\n"
        f"📂 {parsed.get('category', '')}\n"
        f"🆔 ID: #{tx.id}",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()


@router.callback_query(F.data == "cancel_tx")
async def cancel_transaction(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Tranzaksiya bekor qilindi.",
        reply_markup=main_menu_keyboard(),
    )


# Inline button handlers for menu
@router.callback_query(F.data == "cmd_kirim")
async def inline_kirim(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TransactionStates.waiting_for_income_input)
    await callback.message.edit_text(
        "📥 *Daromad kiritish*\n\n"
        "Summani va tavsifni yozing.\n"
        "Misol: `500000 non sotdim`",
        parse_mode="Markdown",
        reply_markup=back_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "cmd_chiqim")
async def inline_chiqim(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TransactionStates.waiting_for_expense_input)
    await callback.message.edit_text(
        "📤 *Xarajat kiritish*\n\n"
        "Summani va tavsifni yozing.\n"
        "Misol: `1000000 benzin oldim`",
        parse_mode="Markdown",
        reply_markup=back_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "cmd_last10")
async def inline_last10(callback: CallbackQuery):
    transactions = await get_transactions(callback.from_user.id)
    if not transactions:
        await callback.message.edit_text(
            "📋 Hech qanday tranzaksiya topilmadi.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    lines = ["📋 *Oxirgi tranzaksiyalar:*\n"]
    for tx in transactions[:10]:
        emoji = "📥" if tx.type == TransactionType.INCOME else "📤"
        date_str = tx.created_at.strftime("%m/%d %H:%M") if tx.created_at else ""
        lines.append(
            f"{emoji} {tx.amount:,.0f} UZS — {tx.item or 'N/A'} "
            f"({tx.category or 'N/A'}) _{date_str}_"
        )

    await callback.message.edit_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🤖 *HisoblBot — Asosiy menyu*",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()
