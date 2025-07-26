import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram.ext import Application
from src.config import TELEGRAM_BOT_TOKEN, LOG_LEVEL
from src.telegram.handlers import TelegramHandlers
from src.zenon.websocket import ZenonWebSocket
from database import init_database

# Create logs directory
LOGS_DIR = Path('logs')
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging with file handler
log_level = getattr(logging, LOG_LEVEL.upper()) if LOG_LEVEL else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS_DIR / 'bot.log')
    ]
)

# Enable debug logging for WebSocket and decoder
if LOG_LEVEL and LOG_LEVEL.upper() == 'DEBUG':
    logging.getLogger('src.zenon.websocket').setLevel(logging.DEBUG)
    logging.getLogger('src.zenon.decoder').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

class ZenonBridgeBot:
    """Main bot class that coordinates Telegram and WebSocket components."""
    
    def __init__(self):
        self.application = None
        self.handlers = TelegramHandlers()
        self.websocket = None
        self.running = False
    
    async def on_transaction(self, tx_info):
        """Callback for new transactions from WebSocket."""
        logger.info(f"New transaction: {tx_info['type']} - {tx_info['hash']}")
        await self.handlers.send_transaction_notification(self.application, tx_info)
    
    async def initialize(self):
        """Initialize bot components."""
        # Check for bot token
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        # Initialize database
        await init_database()
        
        # Create Telegram application
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Register handlers
        self.handlers.register_handlers(self.application)
        
        # Create WebSocket client
        self.websocket = ZenonWebSocket(self.on_transaction)
        
        logger.info("Bot initialized successfully")
    
    async def start(self):
        """Start the bot."""
        self.running = True
        
        # Initialize application
        await self.application.initialize()
        await self.application.start()
        
        # Start polling for Telegram updates
        await self.application.updater.start_polling(drop_pending_updates=True)
        
        # Update WebSocket status in handlers
        self.handlers.set_ws_status(True)
        
        logger.info("Bot started successfully")
        
        # Start WebSocket connection in background
        websocket_task = asyncio.create_task(self.websocket.start())
        
        try:
            # Keep bot running
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await self.stop()
            websocket_task.cancel()
    
    async def stop(self):
        """Stop the bot gracefully."""
        self.running = False
        
        logger.info("Stopping bot...")
        
        # Stop WebSocket
        if self.websocket:
            await self.websocket.stop()
        
        # Stop Telegram application
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        
        logger.info("Bot stopped")

async def main():
    """Main entry point."""
    bot = ZenonBridgeBot()
    
    try:
        await bot.initialize()
        await bot.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)