import os
import json
import logging
from typing import Dict

# Set up logging
logger = logging.getLogger(__name__)

# Telegram Bot Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

# Admin user IDs (verified)
ADMIN_IDS = [7715819534, 5545933865]  # List of admin Telegram user IDs

# Validate admin IDs
if not ADMIN_IDS:
    raise ValueError("No admin IDs configured. At least one admin ID is required.")
for admin_id in ADMIN_IDS:
    if not isinstance(admin_id, int):
        raise ValueError(f"Invalid admin ID format: {admin_id}. Admin IDs must be integers.")

# Payment methods and details
PAYMENT_METHODS = ["TeleBirr", "CBE"]

PAYMENT_DETAILS = {
    "TeleBirr": {
        "phone": "096139850",
        "name": "Abdisa Feleke"
    },
    "CBE": {
        "account": "010000006623",
        "name": "Abdisa Feleke"
    }
}

# Order statuses
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_COMPLETED = "completed"

# Bot messages
WELCOME_MESSAGE = """
🌟 Welcome to Telegram Premium Service Bot! 🌟

✨ Your Gateway to Premium Features:
• Upload files up to 4GB
• Download files at maximum speed
• Access exclusive stickers
• Create custom emoji
• Voice-to-text conversion
• Ad-free experience
• Premium badge & profile

💫 Get started:
• /menu - Browse available plans
• /help - View all commands
• Contact support for assistance

Start your premium journey today! 🚀
"""

HELP_MESSAGE = """
Available commands:
/start - Start the bot
/menu - Show main menu
/help - Show this help message
/admin_help - Show admin commands (admin only)

Use the buttons below to navigate through the bot's features.
"""