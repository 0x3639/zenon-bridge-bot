import json
import random
import os
from typing import Dict, List
from datetime import datetime
from pathlib import Path
from src.config import ETHERSCAN_BASE_URL, ZENONHUB_BASE_URL, TRANSACTION_TYPES

class MessageFormatter:
    """Format transaction data into Telegram messages."""
    
    def __init__(self):
        self.type_emojis = {
            TRANSACTION_TYPES['WRAP_TOKEN']: '🔄',
            TRANSACTION_TYPES['UNWRAP_TOKEN']: '🔓',
            TRANSACTION_TYPES['REDEEM']: '💰',
            TRANSACTION_TYPES['TRANSFER']: '➡️',
            TRANSACTION_TYPES['UPDATE_WRAP_REQUEST']: '🔄',
            'Unknown': '❓'
        }
        
        self.token_symbols = {
            'zts1znnxxxxxxxxxxxxx9z4ulx': 'ZNN',
            'zts1qsrxxxxxxxxxxxxxmrhjll': 'QSR'
        }
        
        # Load custom messages
        self.wrap_messages = self._load_messages('wrap_messages.json')
        self.unwrap_messages = self._load_messages('unwrap_messages.json')
    
    def _load_messages(self, filename: str) -> List[Dict]:
        """Load custom messages from JSON file."""
        try:
            # Get path relative to project root
            project_root = Path(__file__).parent.parent.parent
            messages_path = project_root / 'messages' / filename
            
            if messages_path.exists():
                with open(messages_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"Warning: Messages file {filename} not found")
                return []
        except Exception as e:
            print(f"Error loading messages from {filename}: {e}")
            return []
    
    def _get_custom_message(self, tx_type: str) -> str:
        """Get a random custom message for the transaction type."""
        try:
            if tx_type == TRANSACTION_TYPES['WRAP_TOKEN'] and self.wrap_messages:
                message_data = random.choice(self.wrap_messages)
                return f"\n💭 *{message_data['message']}*\n   — {message_data['author']}\n"
            elif tx_type == TRANSACTION_TYPES['UNWRAP_TOKEN'] and self.unwrap_messages:
                message_data = random.choice(self.unwrap_messages)
                return f"\n💭 *{message_data['message']}*\n   — {message_data['author']}\n"
        except Exception as e:
            print(f"Error getting custom message: {e}")
        
        return ""
    
    def format_transaction(self, tx: Dict) -> str:
        """Format a transaction into a Telegram message."""
        emoji = self.type_emojis.get(tx.get('type', 'Unknown'), '❓')
        tx_type = tx.get('type', 'Unknown')
        
        # Build message parts
        lines = [
            f"{emoji} **{tx_type} Transaction**",
            ""
        ]
        
        # Add amount and token if available
        if tx.get('formatted_amount') and tx.get('token'):
            token_symbol = self.token_symbols.get(tx['token'], tx['token'][:8])
            lines.append(f"💎 Amount: {tx['formatted_amount']} {token_symbol}")
        
        # Add addresses
        if tx.get('from_addr'):
            lines.append(f"📤 From: {self._format_zts_address(tx['from_addr'])}")
        if tx.get('to_addr'):
            lines.append(f"📥 To: {self._format_zts_address(tx['to_addr'])}")
        
        # Add ETH address if present
        if tx.get('eth_addr'):
            lines.append("")
            lines.append(f"🔗 ETH Address: `{self._short_address(tx['eth_addr'])}`")
            lines.append(f"[View on Etherscan]({ETHERSCAN_BASE_URL}/address/{tx['eth_addr']})")
        
        # Add transaction details
        lines.extend([
            "",
            "📊 **Transaction Details**",
            f"Hash: `{self._short_hash(tx['hash'])}`",
            f"[View on ZenonHub]({ZENONHUB_BASE_URL}/explorer/transaction/{tx['hash']})"
        ])
        
        # Add timestamp if available
        if tx.get('timestamp'):
            lines.append(f"🕐 Time: {tx['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Add custom message for wrap/unwrap transactions
        custom_message = self._get_custom_message(tx_type)
        if custom_message:
            lines.append(custom_message)
        
        return "\n".join(lines)
    
    def format_stats(self, stats: List[Dict], period_days: int) -> str:
        """Format statistics into a message."""
        lines = [
            f"📈 **Bridge Statistics ({period_days} day{'s' if period_days > 1 else ''})**",
            ""
        ]
        
        # Group stats by transaction type
        stats_by_type = {}
        total_count = 0
        
        for stat in stats:
            tx_type = stat['type']
            if tx_type not in stats_by_type:
                stats_by_type[tx_type] = {'count': 0, 'volume': {}}
            
            stats_by_type[tx_type]['count'] += stat['count']
            total_count += stat['count']
            
            if stat['token'] and stat['volume']:
                token_symbol = self.token_symbols.get(stat['token'], stat['token'][:8])
                stats_by_type[tx_type]['volume'][token_symbol] = stat['volume']
        
        # Format by type
        for tx_type, data in stats_by_type.items():
            emoji = self.type_emojis.get(tx_type, '❓')
            lines.append(f"{emoji} **{tx_type}**: {data['count']} transactions")
            
            # Add volume info
            for token, volume in data['volume'].items():
                if volume:
                    lines.append(f"  └─ {volume:,.2f} {token}")
        
        lines.extend([
            "",
            f"📊 **Total**: {total_count} transactions"
        ])
        
        return "\n".join(lines)
    
    def format_help(self) -> str:
        """Format help message."""
        return """
🤖 **Zenon Bridge Alert Bot**

Monitor Zenon Bridge wrapping and unwrapping activity in real-time!

**Available Commands:**
/start - Subscribe to bridge notifications
/stop - Unsubscribe from notifications
/stats - View bridge statistics
/status - Check bot connection status
/filter - Set notification filters
/help - Show this help message

**Monitored Transaction Types:**
🔄 WrapToken - Wrapping ZNN/QSR tokens to bridge
🔓 UnwrapToken - Unwrapping tokens from bridge
💰 Redeem - Redeeming bridged tokens

**Links:**
[ZenonHub Explorer](https://zenonhub.io)
[Etherscan](https://etherscan.io)
"""
    
    def format_status(self, is_connected: bool, subscriber_count: int) -> str:
        """Format status message."""
        status = "✅ Connected" if is_connected else "❌ Disconnected"
        
        bridge_address = 'z1qxemdeddedxdrydgexxxxxxxxxxxxxxxmqgr0d'
        
        return f"""
🔌 **Bot Status**

WebSocket: {status}
Active Subscribers: {subscriber_count}
Bridge Address: {self._format_zts_address(bridge_address)}
"""
    
    def _short_address(self, address: str) -> str:
        """Shorten address for display with new format."""
        if len(address) > 16:
            return f"{address[:10]}...{address[-8:]}"
        return address
    
    def _format_zts_address(self, address: str, context: str = "") -> str:
        """Format ZTS address as clickable link to ZenonHub."""
        short_addr = self._short_address(address)
        return f"[{short_addr}]({ZENONHUB_BASE_URL}/explorer/account/{address})"
    
    def _short_hash(self, hash: str) -> str:
        """Shorten transaction hash for display."""
        if len(hash) > 16:
            return f"{hash[:10]}...{hash[-8:]}"
        return hash