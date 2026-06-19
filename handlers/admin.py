import json

from telegram import Update
from telegram.ext import ContextTypes

import config
import excel_loader
from messages import MESSAGES
from handlers import is_whitelisted, get_user_role, main_menu_keyboard


async def reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_whitelisted(update.effective_user.id):
        await update.message.reply_text(MESSAGES["access_denied"])
        return

    if get_user_role(update.effective_user.id) != "admin":
        await update.message.reply_text("فقط مدیران می‌توانند این دستور را اجرا کنند.")
        return

    success = excel_loader.reload()
    if success:
        await update.message.reply_text(
            MESSAGES["reload_success"].format(count=len(excel_loader.cache.boards)),
            reply_markup=main_menu_keyboard(),
        )
    else:
        await update.message.reply_text(MESSAGES["reload_failed"])


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_whitelisted(update.effective_user.id):
        await update.message.reply_text(MESSAGES["access_denied"])
        return

    last = excel_loader.cache.last_loaded
    time_str = last.strftime("%Y/%m/%d %H:%M") if last else "هرگز"
    boards = excel_loader.cache.boards
    available = len([b for b in boards if b.status == "خالی"])
    occupied = len([b for b in boards if b.status == "پر"])

    await update.message.reply_text(
        MESSAGES["status_info"].format(
            time=time_str,
            total=len(boards),
            available=available,
            occupied=occupied,
        ),
        reply_markup=main_menu_keyboard(),
    )


async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_whitelisted(update.effective_user.id):
        await update.message.reply_text(MESSAGES["access_denied"])
        return

    if get_user_role(update.effective_user.id) != "admin":
        await update.message.reply_text("فقط مدیران می‌توانند این دستور را اجرا کنند.")
        return

    if not context.args:
        await update.message.reply_text("لطفاً آیدی عددی کاربر را وارد کنید.\nمثال: /add_user 123456789")
        return

    user_id = int(context.args[0])
    try:
        with open(config.WHITELIST_PATH, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"users": []}

    users = data.get("users", [])
    # Normalize to list of ints
    if users and isinstance(users[0], dict):
        existing = [u["telegram_id"] for u in users]
    else:
        existing = [u for u in users if isinstance(u, int)]

    if user_id in existing:
        await update.message.reply_text(f"کاربر {user_id} از قبل در لیست است.")
        return

    users.append(user_id)
    data["users"] = users
    with open(config.WHITELIST_PATH, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(MESSAGES["admin_added"].format(user_id=user_id))


async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_whitelisted(update.effective_user.id):
        await update.message.reply_text(MESSAGES["access_denied"])
        return

    if get_user_role(update.effective_user.id) != "admin":
        await update.message.reply_text("فقط مدیران می‌توانند این دستور را اجرا کنند.")
        return

    if not context.args:
        await update.message.reply_text("لطفاً آیدی عددی کاربر را وارد کنید.\nمثال: /remove_user 123456789")
        return

    user_id = int(context.args[0])
    try:
        with open(config.WHITELIST_PATH, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        await update.message.reply_text(MESSAGES["admin_not_found"].format(user_id=user_id))
        return

    users = data.get("users", [])
    original_len = len(users)

    # Normalize to list of ints
    if users and isinstance(users[0], dict):
        users = [u["telegram_id"] for u in users if u["telegram_id"] != user_id]
    else:
        users = [u for u in users if isinstance(u, int) and u != user_id]

    if len(users) == original_len:
        await update.message.reply_text(MESSAGES["admin_not_found"].format(user_id=user_id))
        return

    data["users"] = users
    with open(config.WHITELIST_PATH, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(MESSAGES["admin_removed"].format(user_id=user_id))
