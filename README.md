git clone https://github.com/yourusername/telegram-premium-bot.git
cd telegram-premium-bot
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Copy the example environment file and configure your settings:
```bash
cp .env.example .env
```

4. Edit `.env` file with your configuration:
```
BOT_TOKEN=your_bot_token_here
SESSION_SECRET=your_session_secret_here
ADMIN_IDS=your_telegram_user_id
```

## Configuration

### Admin Setup

1. Set up admin users in `.env`:
```
ADMIN_IDS=123456789,987654321  # Replace with actual admin IDs
```

2. Configure payment methods and details in `config.py`:
```python
PAYMENT_METHODS = ["TeleBirr", "CBE"]
PAYMENT_DETAILS = {
    "TeleBirr": {
        "phone": "your_phone",
        "name": "your_name"
    },
    "CBE": {
        "account": "your_account",
        "name": "your_name"
    }
}
```

### Environment Variables

- `BOT_TOKEN`: Your Telegram Bot API token
- `SESSION_SECRET`: A secure random string for session management
- `ADMIN_IDS`: Comma-separated list of admin Telegram user IDs
- `DEBUG_MODE`: Enable/disable debug mode (optional)
- `ENABLE_LOGGING`: Enable/disable detailed logging (optional)
- `PAYMENT_PROCESSING_ENABLED`: Enable/disable payment features (optional)

## Usage

### Admin Commands

- `/admin_help` - Show admin help message
- `/set_welcome_image` - Set custom welcome image
- `/add_service` - Add or update a service (Format: /add_service name price)
- `/remove_service` - Remove a service (Format: /remove_service name)
- `/list_services` - List all services and prices

### User Commands

- `/start` - Start the bot
- `/menu` - Show available services
- `/help` - Show help message

## Running the Bot

1. Start the bot:
```bash
python bot.py