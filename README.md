# Zenon Bridge Alert Bot

[![CI](https://github.com/0x3639/zenon-bridge-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/0x3639/zenon-bridge-bot/actions/workflows/ci.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-supported-blue.svg)](https://www.docker.com/)

A Telegram bot that monitors all activity on the Zenon Bridge in real-time and sends notifications for bridge transactions.

## Features

- 🔄 Real-time monitoring of bridge transactions
- 📱 Telegram notifications for all bridge activity
- 💭 Random custom messages for wrap/unwrap transactions
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

## Custom Messages

The bot includes fun, randomly selected custom messages for wrap and unwrap transactions to make notifications more engaging! Each message includes an author attribution and a unique perspective on the bridging experience.

### Message Examples

**Wrap Transaction Messages:**
- "Another brave soul ventures into the multiverse! 🌌" — 0x3639
- "Bridging the gap between worlds, one transaction at a time! 🌉" — ZenonCommunity

**Unwrap Transaction Messages:**
- "Welcome back to the Network of Momentum! 🏠" — 0x3639
- "Your tokens are coming home to Zenon! 🌟" — ZenonCommunity

### Adding Your Own Messages

Want to contribute fun messages to the bot? We welcome community contributions!

**How to submit new messages:**

1. **Fork the repository** on GitHub
2. **Edit the message files:**
   - For wrap messages: `messages/wrap_messages.json`
   - For unwrap messages: `messages/unwrap_messages.json`
3. **Add your message** following this format:
   ```json
   {
     "author": "YourUsername",
     "message": "Your creative message here! 🚀"
   }
   ```
4. **Submit a Pull Request** with:
   - **Title:** "Add custom messages for [wrap/unwrap] transactions"
   - **Description:** Brief explanation of your messages
   - **Guidelines:** Keep messages fun, positive, and bridge-related!

**Message Guidelines:**
- ✅ Keep it fun and positive
- ✅ Bridge/interchain/multiverse themes preferred
- ✅ Include relevant emojis
- ✅ Keep under 100 characters for readability
- ❌ No inappropriate or offensive content
- ❌ No promotional/spam content

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

### Docker Run Method

```bash
# Build image
docker build -t zenon-bridge-bot .

# Create data directory
mkdir -p data

# Run container
docker run -d \
  --name zenon-bridge-bot \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN=your_token_here \
  -v $(pwd)/data:/app/data \
  zenon-bridge-bot:latest
```

### Docker Compose Method (Recommended)

```bash
# Create .env file with your token
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env

# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

### Troubleshooting Docker Deployment

**Container exits immediately:**
```bash
# Check logs
docker logs zenon-bridge-bot

# Common issues:
# - Missing TELEGRAM_BOT_TOKEN
# - Database permission issues - ensure data directory exists
# - Port conflicts - remove existing containers
```

**Container name conflict:**
```bash
# Stop and remove existing container
docker stop zenon-bridge-bot
docker rm zenon-bridge-bot

# Or force remove
docker rm -f zenon-bridge-bot
```

**Remote server deployment:**
```bash
# Use sudo if needed
sudo docker ps -a | grep zenon
sudo docker logs zenon-bridge-bot
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
├── messages/                  # Custom messages for transactions
│   ├── wrap_messages.json     # Messages for wrap transactions
│   └── unwrap_messages.json   # Messages for unwrap transactions
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