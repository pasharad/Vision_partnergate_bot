from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import excel_loader
from messages import MESSAGES, BOARD_ROW
from utils import rial_to_toman_short
from handlers import is_whitelisted, main_menu_keyboard


def _status_icon(status: str) -> str:
    return "\U0001f7e2" if status == "خالی" else "\U0001f534"


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_whitelisted(query.from_user.id):
        await query.answer(MESSAGES["access_denied"], show_alert=True)
        return

    await query.edit_message_text(MESSAGES["search_prompt"])
    context.user_data["awaiting_search"] = True


async def search_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_search"):
        return

    context.user_data["awaiting_search"] = False
    text = update.message.text

    if not text or text.startswith("/"):
        return

    boards = excel_loader.cache.search(text)
    if not boards:
        await update.message.reply_text(
            MESSAGES["no_results"],
            reply_markup=main_menu_keyboard(),
        )
        return

    lines = [f"\U0001f50d نتایج جستجو برای \"{text}\" ({len(boards)} مورد)\n"]
    for b in boards[:20]:
        lines.append(BOARD_ROW.format(
            status_icon=_status_icon(b.status),
            code=b.board_code,
            station=b.station,
            city=b.city,
            mode=b.mode,
            price=rial_to_toman_short(b.price_monthly),
        ))

    if len(boards) > 20:
        lines.append(f"\n... و {len(boards) - 20} نتیجه دیگر")

    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=main_menu_keyboard(),
    )


async def details_by_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_whitelisted(update.effective_user.id):
        await update.message.reply_text(MESSAGES["access_denied"])
        return

    args = context.args
    if not args:
        await update.message.reply_text("لطفاً کد تابلو را وارد کنید.\nمثال: /details ab-0")
        return

    code = args[0]
    board = excel_loader.cache.get_by_code(code)
    if not board:
        await update.message.reply_text(f"تابلو با کد «{code}» یافت نشد.")
        return

    from messages import BOARD_DETAIL
    from utils import format_area

    text = BOARD_DETAIL.format(
        code=board.board_code,
        station=board.station,
        city=board.city,
        status=f"{_status_icon(board.status)} {board.status}",
        mode=board.mode,
        area=format_area(board.area_sqm),
        price_monthly=rial_to_toman_short(board.price_monthly),
        price_2month=rial_to_toman_short(board.price_2month),
        price_3_5month=rial_to_toman_short(board.price_3_5month),
        price_6_8month=rial_to_toman_short(board.price_6_8month),
        print_cost=rial_to_toman_short(board.print_total_cost),
        reservation_end=board.reservation_end,
    )
    await update.message.reply_text(text, reply_markup=main_menu_keyboard())
