import logging

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

import config
import excel_loader
from handlers import start, help_command
from handlers.boards import available, occupied, prices, details, back_to_menu, stations_list, station_boards, filter_menu
from handlers.search import search_command, search_results, details_by_code
from handlers.admin import reload_command, status_command, add_user, remove_user

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def scheduled_reload(context):
    excel_loader.reload()
    logger.info(f"Scheduled reload: {len(excel_loader.cache.boards)} boards")


def main():
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set. Check your .env file.")
        return

    if not excel_loader.load():
        logger.error("Failed to load Excel on startup.")
        return

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reload", reload_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("add_user", add_user))
    app.add_handler(CommandHandler("remove_user", remove_user))
    app.add_handler(CommandHandler("details", details_by_code))

    # Callback query handlers (inline buttons)
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))
    app.add_handler(CallbackQueryHandler(search_command, pattern="^search$"))
    app.add_handler(CallbackQueryHandler(available, pattern="^available:"))
    app.add_handler(CallbackQueryHandler(occupied, pattern="^occupied:"))
    app.add_handler(CallbackQueryHandler(prices, pattern="^prices:"))
    app.add_handler(CallbackQueryHandler(details, pattern="^detail:"))
    app.add_handler(CallbackQueryHandler(stations_list, pattern="^stations:"))
    app.add_handler(CallbackQueryHandler(station_boards, pattern="^station:"))
    app.add_handler(CallbackQueryHandler(filter_menu, pattern="^filter_menu:"))

    # Message handler for search input
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        search_results,
    ))

    # Schedule periodic reload using built-in job queue
    app.job_queue.run_repeating(
        scheduled_reload,
        interval=config.RELOAD_INTERVAL_HOURS * 3600,
        first=10,
    )

    logger.info(f"Bot started. Loaded {len(excel_loader.cache.boards)} boards.")
    app.run_polling()


if __name__ == "__main__":
    main()
