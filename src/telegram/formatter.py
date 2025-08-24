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
            TRANSACTION_TYPES['WRAP_TOKEN']: '🎁',
            TRANSACTION_TYPES['UNWRAP_TOKEN']: '📦',
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
        
        # Get token and amount info
        token = tx.get('token', '')
        token_symbol = self.token_symbols.get(token, token[:8] if token else 'Unknown')
        amount = tx.get('amount', '0')
        formatted_amount = tx.get('formatted_amount', '')
        
        # Create a more descriptive title based on transaction type
        if tx_type == 'WrapToken':
            action_text = "Bridge Wrap"
        elif tx_type == 'UnwrapToken':
            action_text = "Bridge Unwrap"
        elif tx_type == 'Redeem':
            action_text = "Bridge Redeem"
        else:
            action_text = tx_type
        
        # Build message with prominent amount display
        lines = []
        
        # Header with transaction type and amount
        if formatted_amount and amount != '0':
            lines.extend([
                f"{emoji} **{action_text}**",
                f"",
                f"💎 **{formatted_amount} {token_symbol}**",
                ""
            ])
        else:
            lines.extend([
                f"{emoji} **{action_text}**",
                ""
            ])
        
        # Add addresses with better formatting
        from_addr = tx.get('from_addr', '')
        to_addr = tx.get('to_addr', '')
        bridge_addr = 'z1qxemdeddedxdrydgexxxxxxxxxxxxxxxmqgr0d'
        
        if tx_type == 'WrapToken':
            # User wrapping tokens - sending TO bridge
            lines.append(f"👤 User: {self._format_zts_address(from_addr)}")
            lines.append(f"🌉 → Bridge")
        elif tx_type == 'UnwrapToken':
            # Bridge unwrapping tokens - sending FROM bridge to user
            lines.append(f"🌉 Bridge →")
            lines.append(f"👤 User: {self._format_zts_address(to_addr)}")
        elif tx_type == 'Redeem':
            # Redeem operation
            if from_addr == bridge_addr:
                lines.append(f"🌉 Bridge →")
                lines.append(f"👤 User: {self._format_zts_address(to_addr)}")
            else:
                lines.append(f"👤 User: {self._format_zts_address(from_addr)}")
                lines.append(f"🌉 → Bridge")
        else:
            # Default format for other types
            if from_addr:
                lines.append(f"📤 From: {self._format_zts_address(from_addr)}")
            if to_addr:
                lines.append(f"📥 To: {self._format_zts_address(to_addr)}")
        
        # Add ETH address if present (for cross-chain operations)
        if tx.get('eth_addr'):
            lines.extend([
                "",
                f"🔗 ETH: `{self._short_address(tx['eth_addr'])}`",
                f"[View on Etherscan]({ETHERSCAN_BASE_URL}/address/{tx['eth_addr']})"
            ])
        
        # Add transaction hash as clickable link
        lines.extend([
            "",
            f"🔍 [{self._short_hash(tx['hash'])}]({ZENONHUB_BASE_URL}/explorer/transaction/{tx['hash']}/data)"
        ])
        
        # Add timestamp if available
        if tx.get('timestamp'):
            lines.append(f"⏱ {tx['timestamp'].strftime('%H:%M:%S UTC')}")
        
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
        
        # Define cleaner type labels
        type_labels = {
            'WrapToken': 'Wraps',
            'UnwrapToken': 'Unwraps', 
            'Redeem': 'Redeems',
            'Transfer': 'Transfers'  # In case old data exists
        }
        
        # Show only the transaction types we care about, in order
        priority_types = ['WrapToken', 'UnwrapToken', 'Redeem']
        
        # First show priority types
        for tx_type in priority_types:
            if tx_type in stats_by_type:
                data = stats_by_type[tx_type]
                label = type_labels.get(tx_type, tx_type)
                lines.append(f"- **{label}**: {data['count']}")
                
                # Add volume info if available
                for token, volume in data['volume'].items():
                    if volume:
                        lines.append(f"  └─ {volume:,.0f} {token}")
        
        # If no priority types found, show whatever we have
        if not any(tx_type in stats_by_type for tx_type in priority_types):
            for tx_type, data in stats_by_type.items():
                label = type_labels.get(tx_type, tx_type)
                lines.append(f"- **{label}**: {data['count']}")
        
        lines.extend([
            "",
            f"**Total**: {total_count} transactions"
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
🎁 WrapToken - Wrapping ZNN/QSR tokens to bridge
📦 UnwrapToken - Unwrapping tokens from bridge
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