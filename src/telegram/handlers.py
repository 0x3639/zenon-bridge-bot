import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from typing import Dict
from database import Database
from src.telegram.formatter import MessageFormatter
from src.config import TRANSACTION_TYPES

logger = logging.getLogger(__name__)

class TelegramHandlers:
    """Handle Telegram bot commands and messages."""
    
    def __init__(self):
        self.db = Database()
        self.formatter = MessageFormatter()
        self.ws_connected = False
    
    def set_ws_status(self, connected: bool):
        """Update WebSocket connection status."""
        self.ws_connected = connected
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        await self.db.add_subscriber(user_id, username)
        
        await update.message.reply_text(
            "✅ Welcome to Zenon Bridge Alert Bot!\n\n"
            "You are now subscribed to receive notifications for all bridge transactions.\n\n"
            "Use /help to see available commands.",
            parse_mode='Markdown'
        )
        
        logger.info(f"New subscriber: {user_id} ({username})")
    
    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command."""
        user_id = update.effective_user.id
        
        await self.db.remove_subscriber(user_id)
        
        await update.message.reply_text(
            "❌ You have been unsubscribed from bridge notifications.\n\n"
            "Use /start to subscribe again.",
            parse_mode='Markdown'
        )
        
        logger.info(f"Unsubscribed: {user_id}")
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        # Parse period from command args
        args = context.args
        period_days = 1
        
        if args and args[0].isdigit():
            period_days = int(args[0])
            period_days = min(period_days, 30)  # Max 30 days
        
        stats = await self.db.get_statistics(period_days)
        
        if stats:
            message = self.formatter.format_stats(stats, period_days)
        else:
            message = f"📊 No transactions found in the last {period_days} day{'s' if period_days > 1 else ''}."
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        subscribers = await self.db.get_active_subscribers()
        subscriber_count = len(subscribers)
        
        message = self.formatter.format_status(self.ws_connected, subscriber_count)
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        message = self.formatter.format_help()
        await update.message.reply_text(
            message, 
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    async def filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /filter command."""
        user_id = update.effective_user.id
        args = context.args
        
        # Only allow filtering for wrap, unwrap, and redeem
        ALLOWED_FILTERS = {
            'WRAP_TOKEN': 'WrapToken',
            'UNWRAP_TOKEN': 'UnwrapToken', 
            'REDEEM': 'Redeem'
        }
        
        if not args:
            # Show current filters and available options
            message = (
                "🔧 **Filter Settings**\n\n"
                "Usage: `/filter [type1] [type2] ...`\n"
                "Use `/filter all` to receive all notifications\n\n"
                "**Available Types:**\n"
                "• wraptoken - Token wrapping to bridge\n"
                "• unwraptoken - Token unwrapping from bridge\n"
                "• redeem - Token redemption\n"
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            return
        
        if args[0].lower() == 'all':
            # Clear all filters
            await self.db.update_subscriber_filters(user_id, [])
            await update.message.reply_text(
                "✅ Filters cleared. You will receive all bridge notifications.",
                parse_mode='Markdown'
            )
        else:
            # Set specific filters
            filters = []
            
            for arg in args:
                arg_lower = arg.lower()
                # Find matching transaction type from allowed filters only
                for key, name in ALLOWED_FILTERS.items():
                    if name.lower() == arg_lower:
                        filters.append(name)
                        break
            
            if filters:
                await self.db.update_subscriber_filters(user_id, filters)
                filter_list = '\n'.join([f"• {f}" for f in filters])
                await update.message.reply_text(
                    f"✅ Filters updated. You will only receive notifications for:\n{filter_list}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ No valid transaction types provided. Use /filter to see available types.",
                    parse_mode='Markdown'
                )
    
    async def send_transaction_notification(self, application: Application, tx_info: Dict):
        """Send transaction notification to all active subscribers."""
        subscribers = await self.db.get_active_subscribers()
        message = self.formatter.format_transaction(tx_info)
        
        # Store transaction in database
        await self.db.add_transaction(tx_info)
        
        # Send to each subscriber
        for subscriber in subscribers:
            # Check filters
            filters = subscriber.get('filters', [])
            if filters and tx_info.get('type') not in filters:
                continue
            
            try:
                await application.bot.send_message(
                    chat_id=subscriber['user_id'],
                    text=message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            except Exception as e:
                logger.error(f"Failed to send message to {subscriber['user_id']}: {e}")
    
    def register_handlers(self, application: Application):
        """Register all command handlers."""
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("stop", self.stop))
        application.add_handler(CommandHandler("stats", self.stats))
        application.add_handler(CommandHandler("status", self.status))
        application.add_handler(CommandHandler("help", self.help))
        application.add_handler(CommandHandler("filter", self.filter))