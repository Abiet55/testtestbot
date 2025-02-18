import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import (
    ADMIN_IDS, STATUS_PENDING, STATUS_APPROVED,
    STATUS_REJECTED, STATUS_COMPLETED, WELCOME_MESSAGE, HELP_MESSAGE,
    PAYMENT_DETAILS
)
from storage import Storage
from keyboards import (
    get_services_keyboard,
    get_payment_methods_keyboard,
    get_admin_approval_keyboard,
    get_main_menu_keyboard,
    get_premium_duration_keyboard,
    get_payment_confirmation_keyboard
)
from datetime import datetime

logger = logging.getLogger(__name__)
storage = Storage()

async def is_admin(user_id: int, context: ContextTypes.DEFAULT_TYPE = None) -> bool:
    """Check if a user has admin privileges."""
    logger.info(f"🔒 Admin Access Check - User ID: {user_id}")
    logger.info(f"📋 Current admin IDs: {ADMIN_IDS}")

    is_admin = user_id in ADMIN_IDS
    logger.info(f"🔑 Admin check result for user {user_id}: {'✅ Approved' if is_admin else '❌ Denied'}")

    if context and not is_admin:
        logger.warning(f"⚠️ Unauthorized admin access attempt by user {user_id}")
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ This command is only available to administrators."
        )
    return is_admin

async def set_welcome_image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /set_welcome_image command for admins."""
    user_id = update.message.from_user.id
    logger.info(f"Attempting to set welcome image by user {user_id}")

    if not await is_admin(user_id):
        logger.warning(f"Non-admin user {user_id} attempted to set welcome image")
        return

    # Clear any previous state first
    storage.clear_user_session(user_id)
    storage.set_user_session(user_id, "awaiting_welcome_image", True)

    await update.message.reply_text(
        "🖼️ Please send or forward the image you want to use as welcome image.\n"
        "This image will be shown to new users when they start the bot.\n\n"
        "Note: For best results, use an image with a 16:9 aspect ratio."
    )
    logger.info(f"Admin {user_id} is now in welcome image upload state")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages, including welcome image updates."""
    user_id = update.message.from_user.id
    logger.info(f"Received photo from user {user_id}")

    # Check if user is admin and waiting to set welcome image
    if await is_admin(user_id) and storage.get_user_session(user_id, "awaiting_welcome_image"):
        try:
            # Get the photo with best quality (last in array)
            photo = update.message.photo[-1]
            file_id = photo.file_id
            logger.info(f"Processing welcome image from admin {user_id}, file_id: {file_id}")

            # Store the file_id
            if storage.set_welcome_image(file_id):
                # Clear the awaiting state
                storage.clear_user_session(user_id)  # Clear entire session instead of just the flag

                success_message = (
                    "✅ Welcome image has been updated successfully!\n"
                    "New users will see this image when they start the bot.\n\n"
                    "Preview of how it will appear to new users:"
                )

                await update.message.reply_text(success_message)
                logger.info(f"Welcome image updated by admin {user_id} with file_id: {file_id}")

                # Send a preview of how it will look
                await update.message.reply_photo(
                    photo=file_id,
                    caption=WELCOME_MESSAGE,
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                raise Exception("Failed to store welcome image")

        except IndexError:
            logger.error("No photo found in the message")
            await update.message.reply_text(
                "❌ No valid photo found in your message.\n"
                "Please send a proper image file."
            )
        except Exception as e:
            logger.error(f"Error setting welcome image: {e}")
            await update.message.reply_text(
                "❌ Failed to update welcome image. Please try again later."
            )
        finally:
            # Always clear the awaiting state in case of any errors
            storage.clear_user_session(user_id)  # Clear entire session instead of just the flag

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} started the bot")

    # Get the welcome image file_id
    welcome_image = storage.get_welcome_image()
    logger.info(f"Retrieved welcome image file_id: {welcome_image}")

    try:
        if welcome_image:
            # Send welcome image with caption
            await update.message.reply_photo(
                photo=welcome_image,
                caption=WELCOME_MESSAGE,
                reply_markup=get_main_menu_keyboard()
            )
            logger.info(f"Sent welcome image to user {user_id}")
        else:
            # Fallback to text-only welcome if no image is set
            await update.message.reply_text(
                WELCOME_MESSAGE,
                reply_markup=get_main_menu_keyboard()
            )
            logger.info(f"Sent text-only welcome to user {user_id} (no image set)")
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        # Fallback to text-only welcome if there's an error
        await update.message.reply_text(
            WELCOME_MESSAGE,
            reply_markup=get_main_menu_keyboard()
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command."""
    logger.info(f"User {update.message.from_user.id} requested help")
    await update.message.reply_text(HELP_MESSAGE)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /menu command."""
    logger.info(f"User {update.message.from_user.id} opened the menu")
    await update.message.reply_text(
        "Please select an option:",
        reply_markup=get_main_menu_keyboard()
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries."""
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "place_order":
            await query.message.edit_text(
                "🛍️ Available Services:\n"
                "━━━━━━━━━━━━━━━\n"
                "Please select a service category:",
                reply_markup=get_services_keyboard()
            )

        elif query.data == "telegram_premium":
            await query.message.edit_text(
                "🌟 Telegram Premium Subscription\n"
                "━━━━━━━━━━━━━━━\n"
                "Choose your preferred subscription duration:\n\n"
                "All plans include:\n"
                "• Premium stickers and reactions\n"
                "• 4GB file uploads\n"
                "• Faster downloads\n"
                "• Voice-to-text conversion\n"
                "• Ad-free experience\n"
                "• Unique badge and profile features\n\n"
                "Select a plan that suits you best:",
                reply_markup=get_premium_duration_keyboard()
            )

        elif query.data == "telegram_stars":
            services = storage.get_services()
            stars_price = services.get("Telegram Stars", 0)

            order_id = storage.create_order(query.from_user.id, "Telegram Stars")

            await query.message.edit_text(
                f"⭐ Telegram Stars Service\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📋 Order Details:\n"
                f"🔖 Order ID: {order_id}\n"
                f"📦 Service: Telegram Stars\n"
                f"💰 Price: ${stars_price:.2f}\n"
                f"━━━━━━━━━━━━━━━\n\n"
                f"Your order will be reviewed shortly.",
                reply_markup=get_main_menu_keyboard()
            )

            # Notify admins about the new Stars order
            for admin_id in ADMIN_IDS:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"🔔 New Stars Order\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔖 Order ID: {order_id}\n"
                    f"👤 User ID: {query.from_user.id}\n"
                    f"📦 Service: Telegram Stars\n"
                    f"💰 Price: ${stars_price:.2f}\n"
                    f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"━━━━━━━━━━━━━━━",
                    reply_markup=get_admin_approval_keyboard(order_id, "order")
                )

        elif query.data == "my_orders":
            await handle_order_history(update, context)
            return

        elif query.data.startswith("service_"):
            service_id = query.data.replace("service_", "")
            services = storage.get_services()
            logger.info(f"Service selection - ID: {service_id}, Available services: {services}")

            # Convert callback_data back to service name
            selected_service = None
            for service_name in services.keys():
                if service_name.lower().replace(' ', '_') == service_id:
                    selected_service = service_name
                    break

            if not selected_service:
                await query.message.edit_text(
                    "❌ Service not found or no longer available.\n"
                    "Please try again or contact an administrator.",
                    reply_markup=get_main_menu_keyboard()
                )
                return

            price = storage.get_service_price(selected_service)
            if price is None:
                await query.message.edit_text(
                    "❌ Price not found for this service.\n"
                    "Please try again or contact an administrator.",
                    reply_markup=get_main_menu_keyboard()
                )
                return

            order_id = storage.create_order(query.from_user.id, selected_service)
            logger.info(f"Created order {order_id} for service {selected_service} at price ${price}")

            await query.message.edit_text(
                f"✨ Order Created!\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📋 Order Details:\n"
                f"🔖 Order ID: {order_id}\n"
                f"📦 Service: {selected_service}\n"
                f"💰 Price: ${price:.2f}\n"
                f"━━━━━━━━━━━━━━━\n\n"
                f"Your order will be reviewed shortly.",
                reply_markup=get_main_menu_keyboard()
            )

            # Notify admins
            for admin_id in ADMIN_IDS:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"🔔 New Order\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔖 Order ID: {order_id}\n"
                    f"👤 User ID: {query.from_user.id}\n"
                    f"📦 Service: {selected_service}\n"
                    f"💰 Price: ${price:.2f}\n"
                    f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"━━━━━━━━━━━━━━━",
                    reply_markup=get_admin_approval_keyboard(order_id, "order")
                )

        elif query.data.startswith("payment_"):
            payment_method = query.data.replace("payment_", "")
            user_id = query.from_user.id
            order_id = storage.get_user_session(user_id, "current_order")

            if order_id and storage.update_payment_method(order_id, payment_method):
                order = storage.get_order(order_id)
                payment_info = PAYMENT_DETAILS.get(payment_method, {})

                payment_details = f"\n{payment_method} Payment Details:\n"
                if payment_method == "TeleBirr":
                    payment_details += f"📱 Phone: {payment_info['phone']}\n"
                else:
                    payment_details += f"💳 Account: {payment_info['account']}\n"
                payment_details += f"👤 Name: {payment_info['name']}\n"

                await query.message.edit_text(
                    f"💫 Payment Information\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔖 Order ID: {order_id}\n"
                    f"🛠️ Service: {order['service']}\n"
                    f"💳 Method: {payment_method}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{payment_details}\n"
                    f"Please make the payment and click 'I've Made the Payment' once completed.",
                    reply_markup=get_payment_confirmation_keyboard(payment_method, order_id)
                )

        elif query.data.startswith("confirm_payment_"):
            parts = query.data.split("_", 3)
            if len(parts) == 4:
                _, _, payment_method, order_id = parts
                await handle_payment_confirmation(query, context, payment_method, order_id)

        elif query.data == "telegram_premium":
            services = storage.get_services()
            premium_services = {k: v for k, v in services.items() if k.startswith("Telegram Premium")}

            if not premium_services:
                await query.message.edit_text(
                    "❌ No premium services are currently available.\n"
                    "Please contact an administrator.",
                    reply_markup=get_main_menu_keyboard()
                )
                return

            await query.message.edit_text(
                "🌟 Telegram Premium Services\n"
                "Please select a premium plan:",
                reply_markup=get_premium_duration_keyboard()
            )

        elif query.data.startswith("premium_"):
            duration = query.data.replace("premium_", "")
            duration_display = {
                "1month": "1 Month",
                "3months": "3 Months",
                "6months": "6 Months",
                "1year": "1 Year"
            }

            service_name = f"Telegram Premium - {duration_display[duration]}"
            price = storage.get_service_price(service_name)

            if price is None:
                await query.message.edit_text(
                    "❌ Service not found or price not set.\n"
                    "Please contact an administrator.",
                    reply_markup=get_main_menu_keyboard()
                )
                return

            order_id = storage.create_order(query.from_user.id, service_name)

            await query.message.edit_text(
                f"✨ Premium Order Created!\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📋 Order Details:\n"
                f"🔖 Order ID: {order_id}\n"
                f"📦 Package: {service_name}\n"
                f"💰 Price: ${price}\n"
                f"━━━━━━━━━━━━━━━\n\n"
                f"Your order will be reviewed shortly.",
                reply_markup=get_main_menu_keyboard()
            )

            # Notify admins
            for admin_id in ADMIN_IDS:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"🔔 New Premium Order\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔖 Order ID: {order_id}\n"
                    f"👤 User ID: {query.from_user.id}\n"
                    f"📦 Package: {service_name}\n"
                    f"💰 Price: ${price}\n"
                    f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"━━━━━━━━━━━━━━━",
                    reply_markup=get_admin_approval_keyboard(order_id, "order")
                )

        elif query.data in ["back_to_menu", "back_to_services"]:
            if query.data == "back_to_menu":
                await query.message.edit_text(
                    "Main Menu:",
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                await query.message.edit_text(
                    "🛍️ Please select a service:",
                    reply_markup=get_services_keyboard()
                )

    except Exception as e:
        logger.error(f"Error in handle_callback: {str(e)}")
        try:
            await query.message.edit_text(
                "❌ An error occurred. Please try again or contact support.",
                reply_markup=get_main_menu_keyboard()
            )
        except Exception as edit_error:
            logger.error(f"Failed to send error message: {str(edit_error)}")
            # If edit fails, try sending a new message
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ An error occurred. Please try again or contact support.",
                reply_markup=get_main_menu_keyboard()
            )

async def handle_order_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle viewing order history."""
    user_id = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id
    orders = storage.get_user_orders(user_id)

    if not orders:
        message = ("📋 Order History\n"
                  "━━━━━━━━━━━━━━━\n"
                  "You don't have any orders yet.\n"
                  "Use /menu to place your first order!")
        if update.callback_query:
            await update.callback_query.message.edit_text(
                message,
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=get_main_menu_keyboard()
            )
        return

    # Format orders into a readable message
    message = "📋 Your Order History\n━━━━━━━━━━━━━━━\n\n"
    for order_id, order in orders.items():
        status_emoji = {
            "pending": "⏳",
            "approved": "✅",
            "rejected": "❌",
            "completed": "🎉"
        }.get(order["status"], "❓")

        message += (f"Order ID: {order_id}\n"
                   f"Service: {order['service']}\n"
                   f"Status: {status_emoji} {order['status'].title()}\n"
                   f"Date: {order['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                   "━━━━━━━━━━━━━━━\n\n")

    if update.callback_query:
        await update.callback_query.message.edit_text(
            message,
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=get_main_menu_keyboard()
        )

async def handle_payment_confirmation(query, context, payment_method, order_id):
    if storage.update_order_status(order_id, STATUS_COMPLETED):
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=f"🎉 Payment Verified!\n"
            f"━━━━━━━━━━━━━━━\n"
            f"Your order {order_id} is now complete.\n"
            f"Thank you for your purchase!",
            reply_markup=get_main_menu_keyboard()
        )
        logger.info(f"Payment for order {order_id} confirmed by user {query.from_user.id}")
        await query.message.edit_text(
            f"Payment for order {order_id} has been confirmed.",
            reply_markup=None
        )
    else:
        await query.message.edit_text(
            f"❌ Payment confirmation failed for order {order_id}. Please try again or contact support.",
            reply_markup=None
        )
        logger.error(f"Payment confirmation failed for order {order_id}")

async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    feedback_text = update.message.text
    feedback_id = storage.add_feedback(user_id, feedback_text)

    await update.message.reply_text(
        "✨ Thank you for your feedback!\n"
        "━━━━━━━━━━━━━━━\n"
        "Our team will review it shortly.",
        reply_markup=get_main_menu_keyboard()
    )

    # Notify admins
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"💬 New Feedback\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 User ID: {user_id}\n"
            f"📝 Feedback: {feedback_text}\n"
            f"━━━━━━━━━━━━━━━",
            reply_markup=get_admin_approval_keyboard(str(feedback_id), "feedback")
        )

async def handle_admin_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not await is_admin(user_id):
        logger.warning(f"Unauthorized admin action attempt by user {user_id}")
        return

    try:
        action, item_type, item_id = query.data.split("_", 2)
        logger.info(f"Admin {user_id} performing {action} on {item_type} {item_id}")

        if item_type == "order":
            order = storage.get_order(item_id)
            if not order:
                logger.error(f"Order {item_id} not found for admin approval")
                await query.message.edit_text(
                    "❌ Error: Order not found",
                    reply_markup=None
                )
                return

            if action == "approve":
                storage.update_order_status(item_id, STATUS_APPROVED)
                await context.bot.send_message(
                    chat_id=order["user_id"],
                    text=f"✅ Order Approved!\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔖 Order ID: {item_id}\n"
                    f"Please select your payment method:",
                    reply_markup=get_payment_methods_keyboard()
                )
                storage.set_user_session(order["user_id"], "current_order", item_id)
                logger.info(f"Order {item_id} approved by admin {user_id}")
            else:
                storage.update_order_status(item_id, STATUS_REJECTED)
                await context.bot.send_message(
                    chat_id=order["user_id"],
                    text=f"❌ Order Rejected\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔖 Order ID: {item_id}",
                    reply_markup=get_main_menu_keyboard()
                )
                logger.info(f"Order {item_id} rejected by admin {user_id}")

            await query.message.edit_text(
                f"{item_type.capitalize()} has been {action}d.",
                reply_markup=None
            )

        elif item_type == "payment":
            order = storage.get_order(item_id)
            if not order:
                logger.error(f"Payment verification failed - Order {item_id} not found")
                await query.message.edit_text("❌ Payment verification failed - Order not found")
                return

            if action == "approve":
                storage.update_order_status(item_id, STATUS_COMPLETED)
                await context.bot.send_message(
                    chat_id=order["user_id"],
                    text=f"🎉 Payment Verified!\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"Your order {item_id} is now complete.\n"
                    f"Thank you for your purchase!",
                    reply_markup=get_main_menu_keyboard()
                )
                logger.info(f"Payment for order {item_id} approved by admin {user_id}")
            else:
                await context.bot.send_message(
                    chat_id=order["user_id"],
                    text=f"❌ Payment Verification Failed\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"Order ID: {item_id}\n"
                    f"Please try again or contact support.",
                    reply_markup=get_main_menu_keyboard()
                )
                logger.info(f"Payment for order {item_id} rejected by admin {user_id}")

            await query.message.edit_text(
                f"Payment for order {item_id} has been {action}d.",
                reply_markup=None
            )

    except ValueError:
        logger.error(f"Invalid callback data format: {query.data}")
        await query.message.edit_text(
            "❌ Error: Invalid approval format",
            reply_markup=None
        )

async def help_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /admin_help command."""
    user_id = update.message.from_user.id
    if not await is_admin(user_id):
        logger.warning(f"Non-admin user {user_id} attempted to access admin help")
        await update.message.reply_text(
            "⚠️ This command is only available to administrators."
        )
        return

    admin_help_text = """
🔐 Admin Commands & Features
━━━━━━━━━━━━━━━

📋 Available Commands:
/admin_help - Show this help message
/set_welcome_image - Set a custom welcome image
/add_service - Add or update a service (Format: /add_service name price)
/remove_service - Remove a service (Format: /remove_service name)
/list_services - List all services and their prices

• Service Management:
  - Use /add_service to add new services
  - Use /remove_service to remove services
  - Use /list_services to view all services

• Welcome Image:
  - Send /set_welcome_image
  - Then send/forward the image
  - Image will be shown to new users

💫 Administrative Features:
• Order Management
• User Management
• System Controls

Note: These commands are restricted to authorized administrators only.
"""
    await update.message.reply_text(admin_help_text)
    logger.info(f"Admin help displayed for user {user_id}")

async def add_service_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /add_service command."""
    user_id = update.message.from_user.id
    if not await is_admin(user_id):
        return

    try:
        # Check command format
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "❌ Invalid format. Use:\n/add_service <name> <price>\n"
                "Example: /add_service 'Premium 1 Month' 5.99"
            )
            return

        # Extract price from the last argument
        price = float(args[-1])
        # Join all other arguments as the service name
        name = " ".join(args[:-1])

        if storage.add_service(name, price):
            await update.message.reply_text(
                f"✅ Service added successfully!\n"
                f"Name: {name}\n"
                f"Price: ${price:.2f}"
            )
            logger.info(f"Admin {user_id} added service: {name} at ${price:.2f}")
        else:
            raise Exception("Failed to save service")

    except ValueError:
        await update.message.reply_text("❌ Invalid price format. Please use a valid number.")
    except Exception as e:
        logger.error(f"Error adding service: {e}")
        await update.message.reply_text("❌ Failed to add service. Please try again.")

async def remove_service_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /remove_service command."""
    user_id = update.message.from_user.id
    if not await is_admin(user_id):
        return

    try:
        if not context.args:
            await update.message.reply_text(
                "❌ Please specify the service name.\n"
                "Format: /remove_service <name>"
            )
            return

        name = " ".join(context.args)
        if storage.remove_service(name):
            await update.message.reply_text(f"✅ Service '{name}' removed successfully!")
            logger.info(f"Admin {user_id} removed service: {name}")
        else:
            await update.message.reply_text(f"❌ Service '{name}' not found.")

    except Exception as e:
        logger.error(f"Error removing service: {e}")
        await update.message.reply_text("❌ Failed to remove service. Please try again.")

async def list_services_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /list_services command."""
    user_id = update.message.from_user.id
    if not await is_admin(user_id):
        return

    services = storage.get_services()
    if not services:
        await update.message.reply_text("📋 No services available.")
        return

    message = "📋 Available Services\n━━━━━━━━━━━━━━━\n\n"
    for name, price in services.items():
        message += f"• {name}\n  💰 ${price:.2f}\n\n"

    await update.message.reply_text(message)
    logger.info(f"Admin {user_id} listed all services")