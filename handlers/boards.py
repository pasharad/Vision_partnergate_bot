from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import config
import excel_loader
from messages import MESSAGES, BOARD_DETAIL, BOARD_ROW
from utils import rial_to_toman_short, format_area, paginate
from handlers import is_whitelisted, main_menu_keyboard


def _status_icon(status: str) -> str:
    return "\U0001f7e2" if status == "\u062e\u0627\u0644\u06cc" else "\U0001f534"


def _build_page_keyboard(page: int, total_pages: int, callback_prefix: str) -> list[list[InlineKeyboardButton]]:
    buttons = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("\u27a1\ufe0f \u0642\u0628\u0644\u06cc", callback_data=f"{callback_prefix}:{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("\u2b05\ufe0f \u0628\u0639\u062f\u06cc", callback_data=f"{callback_prefix}:{page + 1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("\U0001f3e0 \u0628\u0627\u0632\u06af\u0634\u062a \u0628\u0647 \u0645\u0646\u0648\u06cc \u0627\u0635\u0644\u06cc", callback_data="back_to_menu")])
    return buttons


def _get_station_config() -> dict:
    """Load station config, normalize station names (strip trailing spaces)."""
    cfg = config.load_station_config()
    stations_cfg = cfg.get("stations", {})
    return {k.strip(): v for k, v in stations_cfg.items()}


def _get_stations(filter_dir: str = "x", filter_postal: str = "x") -> list[dict]:
    """Get unique stations with board counts, optionally filtered."""
    from collections import OrderedDict
    station_cfg = _get_station_config()

    raw = OrderedDict()
    for b in excel_loader.cache.boards:
        key = b.station
        if key not in raw:
            cfg = station_cfg.get(key.strip(), {})
            raw[key] = {
                "name": key,
                "city": b.city,
                "count": 0,
                "available": 0,
                "postal_num": cfg.get("postal_num"),
                "direction": cfg.get("direction"),
            }
        raw[key]["count"] += 1
        if b.status == "\u062e\u0627\u0644\u06cc":
            raw[key]["available"] += 1

    stations = list(raw.values())

    if filter_dir != "x":
        try:
            d = int(filter_dir)
            stations = [s for s in stations if s["direction"] == d]
        except (ValueError, TypeError):
            pass

    if filter_postal != "x":
        try:
            p = int(filter_postal)
            stations = [s for s in stations if s["postal_num"] == p]
        except (ValueError, TypeError):
            pass

    return stations


def _parse_stations_data(data: str) -> tuple[int, str, str]:
    """Parse 'stations:PAGE:D:POSTAL' -> (page, direction, postal)."""
    parts = data.split(":")
    page = int(parts[1]) if len(parts) > 1 else 0
    direction = parts[2] if len(parts) > 2 else "x"
    postal = parts[3] if len(parts) > 3 else "x"
    return page, direction, postal


async def available(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_whitelisted(query.from_user.id):
        await query.answer(MESSAGES["access_denied"], show_alert=True)
        return

    page = int(query.data.split(":")[1]) if ":" in query.data else 0
    boards = excel_loader.cache.get_available()

    if not boards:
        await query.edit_message_text(MESSAGES["no_data"], reply_markup=main_menu_keyboard())
        return

    page_items, total_pages, has_next = paginate(boards, page)
    lines = [f"\U0001f7e2 \u062a\u0627\u0628\u0644\u0648\u0647\u0627\u06cc \u062e\u0627\u0644\u06cc ({len(boards)} \u0645\u0648\u0631\u062f)\n"]
    for b in page_items:
        lines.append(BOARD_ROW.format(
            status_icon=_status_icon(b.status),
            code=b.board_code,
            station=b.station,
            city=b.city,
            mode=b.mode,
            price=rial_to_toman_short(b.price_monthly),
        ))
    text = "\n".join(lines)
    keyboard = _build_page_keyboard(page, total_pages, "available")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def occupied(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_whitelisted(query.from_user.id):
        await query.answer(MESSAGES["access_denied"], show_alert=True)
        return

    page = int(query.data.split(":")[1]) if ":" in query.data else 0
    boards = excel_loader.cache.get_occupied()

    if not boards:
        await query.edit_message_text(MESSAGES["no_data"], reply_markup=main_menu_keyboard())
        return

    page_items, total_pages, has_next = paginate(boards, page)
    lines = [f"\U0001f534 \u062a\u0627\u0628\u0644\u0648\u0647\u0627\u06cc \u067e\u0631 ({len(boards)} \u0645\u0648\u0631\u062f)\n"]
    for b in page_items:
        lines.append(BOARD_ROW.format(
            status_icon=_status_icon(b.status),
            code=b.board_code,
            station=b.station,
            city=b.city,
            mode=b.mode,
            price=rial_to_toman_short(b.price_monthly),
        ))
    text = "\n".join(lines)
    keyboard = _build_page_keyboard(page, total_pages, "occupied")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_whitelisted(query.from_user.id):
        await query.answer(MESSAGES["access_denied"], show_alert=True)
        return

    page = int(query.data.split(":")[1]) if ":" in query.data else 0
    boards = sorted(excel_loader.cache.boards, key=lambda b: b.station)

    page_items, total_pages, has_next = paginate(boards, page)
    lines = [f"\U0001f4b0 \u0644\u06cc\u0633\u062a \u0642\u06cc\u0645\u062a\u200c\u0647\u0627 ({len(boards)} \u062a\u0627\u0628\u0644\u0648)\n"]
    for b in page_items:
        icon = _status_icon(b.status)
        lines.append(f"{icon} {b.board_code} | {b.station}")
        lines.append(f"    \u0645\u0627\u0647\u06cc\u0627\u0646\u0647: {rial_to_toman_short(b.price_monthly)}")
        lines.append(f"    \u06f6-\u06f8 \u0645\u0627\u0647\u0647: {rial_to_toman_short(b.price_6_8month)}")
        lines.append("")

    text = "\n".join(lines)
    keyboard = _build_page_keyboard(page, total_pages, "prices")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_whitelisted(query.from_user.id):
        await query.answer(MESSAGES["access_denied"], show_alert=True)
        return

    code = query.data.split(":")[1] if ":" in query.data else ""
    board = excel_loader.cache.get_by_code(code)
    if not board:
        await query.answer("\u062a\u0627\u0628\u0644\u0648 \u06cc\u0627\u0641\u062a \u0646\u0634\u062f.", show_alert=True)
        return

    station_cfg = _get_station_config().get(board.station.strip(), {})
    postal = station_cfg.get("postal_num")
    direction_code = station_cfg.get("direction")
    direction_label = config.DIRECTION_LABELS.get(direction_code, "\u062a\u0639\u06cc\u06cc\u0646 \u0646\u0634\u062f\u0647") if direction_code else "\u062a\u0639\u06cc\u06cc\u0646 \u0646\u0634\u062f\u0647"

    text = BOARD_DETAIL.format(
        code=board.board_code,
        station=board.station,
        city=board.city,
        postal_num=str(postal) if postal else "\u062a\u0639\u06cc\u06cc\u0646 \u0646\u0634\u062f\u0647",
        direction=direction_label,
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
    keyboard = [
        [InlineKeyboardButton("\u2b05\ufe0f \u0628\u0627\u0632\u06af\u0634\u062a \u0628\u0647 \u062c\u0627\u06cc\u06af\u0627\u0647", callback_data=f"station:{board.station}")],
        [InlineKeyboardButton("\U0001f3e0 \u0645\u0646\u0648\u06cc \u0627\u0635\u0644\u06cc", callback_data="back_to_menu")],
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(MESSAGES["welcome"], reply_markup=main_menu_keyboard())


async def stations_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of stations to pick from, with filter options."""
    query = update.callback_query
    if not is_whitelisted(query.from_user.id):
        await query.answer(MESSAGES["access_denied"], show_alert=True)
        return

    page, filter_dir, filter_postal = _parse_stations_data(query.data)
    stations = _get_stations(filter_dir, filter_postal)

    filter_parts = []
    if filter_dir != "x":
        filter_parts.append(f"\u062c\u0647\u062a: {config.DIRECTION_LABELS.get(int(filter_dir), filter_dir)}")
    if filter_postal != "x":
        filter_parts.append(f"\u0645\u0646\u0637\u0642\u0647: {filter_postal}")
    filter_text = f"\n\u0641\u06cc\u0644\u062a\u0631: {' | '.join(filter_parts)}" if filter_parts else ""

    page_items, total_pages, _ = paginate(stations, page, per_page=8)
    lines = [f"\U0001f4cd \u062c\u0627\u06cc\u06af\u0627\u0647\u200c\u0647\u0627 ({len(stations)} \u0645\u0648\u0631\u062d){filter_text}\n\u06cc\u06a9 \u062c\u0627\u06cc\u06af\u0627\u0647 \u0631\u0627 \u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0646\u06cc\u062f:\n"]

    buttons = []
    for s in page_items:
        label = f"{s['name']} ({s['available']}/{s['count']})"
        buttons.append([InlineKeyboardButton(label, callback_data=f"station:{s['name']}")])

    nav = []
    prefix = f"stations:{{}}:{filter_dir}:{filter_postal}"
    if page > 0:
        nav.append(InlineKeyboardButton("\u27a1\ufe0f \u0642\u0628\u0644\u06cc", callback_data=prefix.format(page - 1)))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("\u2b05\ufe0f \u0628\u0639\u062f\u06cc", callback_data=prefix.format(page + 1)))
    if nav:
        buttons.append(nav)

    buttons.append([
        InlineKeyboardButton("\U0001f50d \u0641\u06cc\u0644\u062a\u0631 \u062c\u0647\u062a", callback_data=f"filter_menu:d:{filter_dir}:{filter_postal}"),
        InlineKeyboardButton("\U0001f4cd \u0641\u06cc\u0644\u062a\u0631 \u0645\u0646\u0637\u0642\u0647", callback_data=f"filter_menu:p:{filter_dir}:{filter_postal}"),
    ])
    if filter_dir != "x" or filter_postal != "x":
        buttons.append([InlineKeyboardButton("\u274c \u067e\u0627\u06a9 \u06a9\u0631\u062f\u0646 \u0641\u06cc\u0644\u062a\u0631\u0647\u0627", callback_data="stations:0:x:x")])
    buttons.append([InlineKeyboardButton("\U0001f3e0 \u0628\u0627\u0632\u06af\u0634\u062a \u0628\u0647 \u0645\u0646\u0648\u06cc \u0627\u0635\u0644\u06cc", callback_data="back_to_menu")])

    await query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))


async def station_boards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show boards at a specific station."""
    query = update.callback_query
    if not is_whitelisted(query.from_user.id):
        await query.answer(MESSAGES["access_denied"], show_alert=True)
        return

    station_name = query.data.split(":", 1)[1] if ":" in query.data else ""
    boards = [b for b in excel_loader.cache.boards if b.station == station_name]

    if not boards:
        await query.answer("\u062c\u0627\u06cc\u06af\u0627\u0647 \u06cc\u0627\u0641\u062a \u0646\u0634\u062f.", show_alert=True)
        return

    lines = [f"\U0001f4cd {station_name} ({len(boards)} \u062a\u0627\u0628\u0644\u0648)\n"]

    buttons = []
    for b in boards:
        icon = _status_icon(b.status)
        label = f"{icon} {b.board_code} - {rial_to_toman_short(b.price_monthly)}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"detail:{b.board_code}")])

    buttons.append([InlineKeyboardButton("\u2b05\ufe0f \u0628\u0627\u0632\u06af\u0634\u062a \u0628\u0647 \u062c\u0627\u06cc\u06af\u0627\u0647\u200c\u0647\u0627", callback_data="stations:0:x:x")])
    buttons.append([InlineKeyboardButton("\U0001f3e0 \u0645\u0646\u0648\u06cc \u0627\u0635\u0644\u06cc", callback_data="back_to_menu")])

    await query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))


async def filter_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show filter options for direction or postal number."""
    query = update.callback_query
    if not is_whitelisted(query.from_user.id):
        await query.answer(MESSAGES["access_denied"], show_alert=True)
        return

    parts = query.data.split(":")
    filter_type = parts[1]
    current_dir = parts[2] if len(parts) > 2 else "x"
    current_postal = parts[3] if len(parts) > 3 else "x"

    back_cb = f"stations:0:{current_dir}:{current_postal}"

    if filter_type == "d":
        lines = ["\U0001f50d \u0641\u06cc\u0644\u062a\u0631 \u0628\u0631 \u0627\u0633\u0627\u0633 \u062c\u0647\u062a \u062c\u063a\u0631\u0627\u0641\u06cc\u0627\u06cc\u06cc:\n"]
        buttons = []
        for code, label in config.DIRECTION_LABELS.items():
            marker = " \u2705" if current_dir == str(code) else ""
            buttons.append([InlineKeyboardButton(
                f"{label}{marker}",
                callback_data=f"stations:0:{code}:{current_postal}",
            )])
        buttons.append([InlineKeyboardButton("\u2b05\ufe0f \u0628\u0627\u0632\u06af\u0634\u062a", callback_data=back_cb)])
    else:
        station_cfg = _get_station_config()
        postals = sorted(set(
            cfg.get("postal_num")
            for cfg in station_cfg.values()
            if cfg.get("postal_num") is not None
        ))
        if not postals:
            postals = list(range(1, 23))

        lines = ["\U0001f4cd \u0641\u06cc\u0644\u062a\u0631 \u0628\u0631 \u0627\u0633\u0627\u0633 \u0645\u0646\u0637\u0642\u0647 \u067e\u0633\u062a\u06cc (\u062a\u0647\u0631\u0627\u0646):\n"]
        buttons = []
        row = []
        for p in postals:
            marker = " \u2705" if current_postal == str(p) else ""
            row.append(InlineKeyboardButton(
                f"{p}{marker}",
                callback_data=f"stations:0:{current_dir}:{p}",
            ))
            if len(row) == 4:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton("\u2b05\ufe0f \u0628\u0627\u0632\u06af\u0634\u062a", callback_data=back_cb)])

    await query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))
