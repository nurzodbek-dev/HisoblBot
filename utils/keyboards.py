from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📥 Kirim", callback_data="cmd_kirim"),
                InlineKeyboardButton(text="📤 Chiqim", callback_data="cmd_chiqim"),
            ],
            [
                InlineKeyboardButton(text="📊 Hisobot", callback_data="cmd_hisobot"),
                InlineKeyboardButton(text="🏛 Soliq", callback_data="cmd_solik"),
            ],
            [
                InlineKeyboardButton(text="📋 Oxirgi 10 ta", callback_data="cmd_last10"),
                InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="cmd_settings"),
            ],
        ]
    )


def report_period_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Haftalik", callback_data="report_weekly"),
                InlineKeyboardButton(text="📅 Oylik", callback_data="report_monthly"),
            ],
            [
                InlineKeyboardButton(text="📅 Yillik", callback_data="report_yearly"),
            ],
            [
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu"),
            ],
        ]
    )


def tax_period_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Oy uchun", callback_data="tax_monthly"),
                InlineKeyboardButton(text="📅 Yil uchun", callback_data="tax_yearly"),
            ],
            [
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu"),
            ],
        ]
    )


def confirm_transaction_keyboard(tx_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_{tx_type}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_tx"),
            ],
        ]
    )


def settings_keyboard(weekly: bool, monthly: bool) -> InlineKeyboardMarkup:
    w_text = "✅ Haftalik hisobot" if weekly else "❌ Haftalik hisobot"
    m_text = "✅ Oylik hisobot" if monthly else "❌ Oylik hisobot"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=w_text, callback_data="toggle_weekly")],
            [InlineKeyboardButton(text=m_text, callback_data="toggle_monthly")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu")],
        ]
    )


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="back_to_menu")],
        ]
    )
