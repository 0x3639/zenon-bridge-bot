import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Zenon Network Configuration
ZENON_WSS_URL = 'wss://my.hc1node.com:35998'
BRIDGE_ADDRESS = 'z1qxemdeddedxdrydgexxxxxxxxxxxxxxxmqgr0d'

# Explorer URLs
ETHERSCAN_BASE_URL = 'https://etherscan.io'
ZENONHUB_BASE_URL = 'https://zenonhub.io'

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', './data/bridge_bot.db')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Transaction Types
TRANSACTION_TYPES = {
    'WRAP_TOKEN': 'WrapToken',
    'UNWRAP_TOKEN': 'UnwrapToken',
    'REDEEM': 'Redeem',
    'TRANSFER': 'Transfer',
    'UPDATE_WRAP_REQUEST': 'UpdateWrapRequest'
}

# Token Information
TOKEN_DECIMALS = {
    'zts1znnxxxxxxxxxxxxx9z4ulx': 8,  # ZNN
    'zts1qsrxxxxxxxxxxxxxmrhjll': 8   # QSR
}