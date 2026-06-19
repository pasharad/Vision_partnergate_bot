from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import config
from messages import MESSAGES


def _load_whitelist() -> list:
    import json
    try:
        with open(config.WHITELIST_PATH, "r") as f:
            data = json.load(f)
        users = data.get("users", [])
        # Support both formats: list of ints or list of dicts
        if users and isinstance(users[0], int):
            return users
        return [u["telegram_id"] for u in users]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def is_whitelisted(user_id: int) -> bool:
    allowed = _load_whitelist()
    if not allowed:
        return True
    return user_id in allowed


def get_user_role(user_id: int) -> str:
    import json
    try:
        with open(config.WHITELIST_PATH, "r") as f:
            data = json.load(f)
        users = data.get("users", [])
        for u in users:
            if isinstance(u, dict) and u.get("telegram_id") == user_id:
                return u.get("role", "client")
            elif isinstance(u, int) and u == user_id:
                return "admin" if len(users) == 1 else "client"
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return "client"


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("تابلوهای خالی", callback_data="available:0"),
            InlineKeyboardButton("تابلوهای پر", callback_data="occupied:0"),
        ],
        [
            InlineKeyboardButton("لیست قیمت‌ها", callback_data="prices:0"),
            InlineKeyboardButton("جزئیات تابلو", callback_data="stations:0"),
        ],
        [
            InlineKeyboardButton("جستجو", callback_data="search"),
        ],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_whitelisted(update.effective_user.id):
        await update.message.reply_text(MESSAGES["access_denied"])
        return
    await update.message.reply_text(
        MESSAGES["welcome"],
        reply_markup=main_menu_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_whitelisted(update.effective_user.id):
        await update.message.reply_text(MESSAGES["access_denied"])
        return
    await update.message.reply_text(MESSAGES["help"])
