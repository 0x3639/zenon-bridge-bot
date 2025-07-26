#!/usr/bin/env python3
"""
Test transaction detection without Telegram
"""

import asyncio
import logging
from datetime import datetime
from src.zenon.websocket import ZenonWebSocket

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Track transactions
transactions_found = []

async def on_transaction(tx_info):
    """Handle new transaction."""
    transactions_found.append(tx_info)
    print(f"\n🎉 TRANSACTION DETECTED at {datetime.now()}")
    print("=" * 80)
    print(f"Type: {tx_info['type']}")
    print(f"Hash: {tx_info['hash']}")
    print(f"From: {tx_info['from_addr']}")
    print(f"To: {tx_info['to_addr']}")
    print(f"Amount: {tx_info.get('formatted_amount', tx_info.get('amount', 'N/A'))}")
    print(f"Token: {tx_info.get('token', 'N/A')}")
    if tx_info.get('eth_addr'):
        print(f"ETH Address: {tx_info['eth_addr']}")
    print("=" * 80)

async def main():
    """Test transaction detection."""
    print("🚀 Testing Zenon Bridge Transaction Detection")
    print("Waiting for transactions... (Press Ctrl+C to stop)")
    print("-" * 80)
    
    # Create WebSocket client
    ws_client = ZenonWebSocket(on_transaction)
    
    try:
        # Run for a while
        await ws_client.start()
    except KeyboardInterrupt:
        print(f"\n\n✅ Test complete. Found {len(transactions_found)} transactions.")
        await ws_client.stop()

if __name__ == "__main__":
    asyncio.run(main())