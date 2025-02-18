from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import PAYMENT_METHODS
from storage import Storage
import logging

logger = logging.getLogger(__name__)
storage = Storage()

def get_services_keyboard():
    """Generate a keyboard with main service categories."""
    keyboard = [
        [InlineKeyboardButton(text="🌟 Telegram Premium", callback_data="telegram_premium")],
        [InlineKeyboardButton(text="⭐ Telegram Stars", callback_data="telegram_stars")]
    ]
    keyboard.append([InlineKeyboardButton(text="↩️ Back to Main Menu", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_premium_duration_keyboard():
    """Generate a keyboard with available premium durations and their prices."""
    keyboard = []
    services = storage.get_services()
    logger.info(f"Retrieved services for premium keyboard: {services}")

    # Define the premium durations and their details
    premium_durations = [
        {"name": "Telegram Premium - 1 Month", "emoji": "1️⃣", "callback": "premium_1month"},
        {"name": "Telegram Premium - 3 Months", "emoji": "3️⃣", "callback": "premium_3months"},
        {"name": "Telegram Premium - 6 Months", "emoji": "6️⃣", "callback": "premium_6months"},
        {"name": "Telegram Premium - 1 Year", "emoji": "🗓️", "callback": "premium_1year"}
    ]

    for duration in premium_durations:
        service_name = duration["name"]
        price = services.get(service_name)
        logger.info(f"Processing {service_name} - Price: ${price if price is not None else 'Not found'}")

        if price is not None:
            description = {
                "Telegram Premium - 1 Month": "Perfect for trying Premium",
                "Telegram Premium - 3 Months": "Most popular choice",
                "Telegram Premium - 6 Months": "Great value package",
                "Telegram Premium - 1 Year": "Best savings deal"
            }.get(service_name, "")

            button_text = f"{duration['emoji']} {service_name.replace('Telegram Premium - ', '')}\n💰 ${price:.2f} - {description}"
            keyboard.append([InlineKeyboardButton(text=button_text, callback_data=duration["callback"])])
            logger.info(f"Added button with text: {button_text}")
        else:
            logger.warning(f"Price not found for service: {service_name}")

    keyboard.append([InlineKeyboardButton(text="↩️ Back", callback_data="back_to_services")])
    return InlineKeyboardMarkup(keyboard)

def get_payment_methods_keyboard():
    keyboard = []
    for method in PAYMENT_METHODS:
        keyboard.append([InlineKeyboardButton(text=f"💳 {method}", callback_data=f"payment_{method}")])
    keyboard.append([InlineKeyboardButton(text="↩️ Back to Main Menu", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_payment_confirmation_keyboard(payment_method: str, order_id: str):
    keyboard = [
        [InlineKeyboardButton(text="✅ I've Made the Payment", 
                            callback_data=f"confirm_payment_{payment_method}_{order_id}")],
        [InlineKeyboardButton(text="❌ Cancel Payment", 
                            callback_data="cancel_payment")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_approval_keyboard(item_id: str, item_type: str):
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Approve", 
                               callback_data=f"approve_{item_type}_{item_id}"),
            InlineKeyboardButton(text="❌ Reject", 
                               callback_data=f"reject_{item_type}_{item_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="🛍️ Place Order", callback_data="place_order")],
        [InlineKeyboardButton(text="📋 My Orders", callback_data="my_orders")],
        [InlineKeyboardButton(text="💬 Submit Feedback", callback_data="submit_feedback")]
    ]
    return InlineKeyboardMarkup(keyboard)