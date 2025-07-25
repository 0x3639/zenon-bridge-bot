# Zenon Bridge Alert Bot

[![CI](https://github.com/0x3639/zenon-bridge-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/0x3639/zenon-bridge-bot/actions/workflows/ci.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-supported-blue.svg)](https://www.docker.com/)

A Telegram bot that monitors all activity on the Zenon Bridge in real-time and sends notifications for bridge transactions.

## Features

- 🔄 Real-time monitoring of bridge transactions
- 📱 Telegram notifications for all bridge activity
- 📊 Transaction statistics (24h, 7d, 30d)
- 🔧 Customizable notification filters
- 🔗 Direct links to ZenonHub and Etherscan
- 💾 Transaction history storage

## Transaction Types

The bot monitors 5 types of bridge transactions:

1. **WrapToken** - Wrapping native tokens to bridge tokens
2. **UnwrapToken** - Unwrapping bridge tokens back to native
3. **Redeem** - Redeeming tokens on destination chain
4. **Transfer** - Bridge token transfers
5. **UpdateWrapRequest** - Updating wrap request status

## Setup

### Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (create via [@BotFather](https://t.me/botfather))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/zenon-bridge-alert.git
cd zenon-bridge-alert
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your Telegram bot token:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
LOG_LEVEL=INFO
DATABASE_PATH=./bridge_bot.db
```

5. Initialize the database:
```bash
python database.py
```

6. Run the bot:
```bash
python src/bot.py
```

## Usage

### Bot Commands

- `/start` - Subscribe to bridge notifications
- `/stop` - Unsubscribe from notifications
- `/stats [days]` - View bridge statistics (default: 1 day, max: 30 days)
- `/status` - Check bot and connection status
- `/filter [types]` - Set notification filters (e.g., `/filter wraptoken redeem`)
- `/filter all` - Clear all filters and receive all notifications
- `/help` - Show help message

### Examples

1. **Subscribe to notifications:**
   ```
   /start
   ```

2. **View 7-day statistics:**
   ```
   /stats 7
   ```

3. **Only receive WrapToken and Redeem notifications:**
   ```
   /filter wraptoken redeem
   ```

4. **Clear filters and receive all notifications:**
   ```
   /filter all
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Required |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `DATABASE_PATH` | Path to SQLite database file | ./bridge_bot.db |

### Network Configuration

The bot connects to the Zenon public node at:
- WebSocket: `wss://my.hc1node.com:35998`
- Bridge Address: `z1qxemdeddedxdrydgexxxxxxxxxxxxxxxmqgr0d`

## Docker Support (Optional)

Build and run with Docker:

```bash
# Build image
docker build -t zenon-bridge-bot .

# Run container
docker run -d \
  --name zenon-bridge-bot \
  -e TELEGRAM_BOT_TOKEN=your_token_here \
  -v ./data:/app/data \
  zenon-bridge-bot
```

## Development

### Project Structure

```
zenon-bridge-alert/
├── src/
│   ├── bot.py                 # Main bot entry point
│   ├── config.py              # Configuration management
│   ├── zenon/
│   │   ├── websocket.py       # WebSocket connection
│   │   └── decoder.py         # Transaction decoder
│   ├── telegram/
│   │   ├── handlers.py        # Command handlers
│   │   └── formatter.py       # Message formatting
│   └── models/
│       └── transactions.py    # Transaction models
├── database.py                # Database setup
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

### Adding New Features

1. To add new transaction types, update:
   - `src/config.py` - Add to `TRANSACTION_TYPES`
   - `src/zenon/decoder.py` - Update detection logic
   - `src/telegram/formatter.py` - Add emoji and formatting

2. To add new commands:
   - Add handler method in `src/telegram/handlers.py`
   - Register handler in `register_handlers()` method

## Troubleshooting

### Bot not receiving messages
- Check bot token is correct
- Ensure you've started the bot with `/start`
- Check WebSocket connection status with `/status`

### WebSocket connection issues
- Verify the node URL is accessible
- Check network connectivity
- Review logs for error messages

### Database errors
- Ensure write permissions for database file
- Run `python database.py` to reinitialize

## Security

- Store bot token securely in `.env` file
- Never commit `.env` to version control
- Use environment variables for sensitive data
- Validate all user inputs

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Zenon Network community
- ZenonHub for explorer services
- Etherscan for Ethereum blockchain data