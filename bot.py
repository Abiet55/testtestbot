import asyncio
import logging
import os
import sys
import signal
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from config import BOT_TOKEN
from handlers import (
    start,
    help_command,
    help_admin_command,
    menu,
    handle_callback,
    handle_feedback,
    handle_admin_approval,
    set_welcome_image_command,
    handle_photo,
    add_service_command,
    remove_service_command,
    list_services_command
)

# Enhanced logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)
PID_FILE = "bot.pid"

def cleanup_pid_file():
    """Remove the PID file."""
    try:
        if os.path.exists(PID_FILE):
            os.unlink(PID_FILE)
            logger.info("PID file removed successfully")
    except Exception as e:
        logger.error(f"Error cleaning up PID file: {e}")

def write_pid_file():
    """Write current process PID to file."""
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"PID file created with PID {os.getpid()}")
    except Exception as e:
        logger.error(f"Error writing PID file: {e}")
        sys.exit(1)

async def init_default_services():
    """Initialize default services if none exist."""
    from storage import Storage
    storage = Storage()
    services = storage.get_services()

    if not services:
        logger.info("No services found, adding default services...")
        default_services = {
            "Telegram Premium - 1 Month": 4.99,
            "Telegram Premium - 3 Months": 12.99,
            "Telegram Premium - 6 Months": 24.99,
            "Telegram Premium - 1 Year": 45.99
        }
        for name, price in default_services.items():
            storage.add_service(name, price)
        logger.info("Default services added successfully")

def setup_handlers(application):
    """Set up all command and message handlers."""
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("set_welcome_image", set_welcome_image_command))
    application.add_handler(CommandHandler("admin_help", help_admin_command))
    application.add_handler(CommandHandler("add_service", add_service_command))
    application.add_handler(CommandHandler("remove_service", remove_service_command))
    application.add_handler(CommandHandler("list_services", list_services_command))

    # Message handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(handle_admin_approval, pattern="^(approve|reject)_"))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback))

def main():
    """Entry point for the bot."""
    try:
        # Write PID file
        write_pid_file()

        # Set up signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda s, f: cleanup_pid_file() or sys.exit(0))

        # Build application
        application = ApplicationBuilder().token(BOT_TOKEN).build()

        # Set up handlers
        setup_handlers(application)

        logger.info("Starting bot...")

        # Run the application
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
    finally:
        cleanup_pid_file()
        logger.info("Bot shutdown complete")

if __name__ == '__main__':
    main()