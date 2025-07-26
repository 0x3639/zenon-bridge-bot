#!/usr/bin/env python3
"""
Test script to monitor all account blocks and debug WebSocket data
"""

import asyncio
import websockets
import json
from datetime import datetime

# Configuration
WSS_URL = 'wss://my.hc1node.com:35998'
BRIDGE_ADDRESS = 'z1qxemdeddedxdrydgexxxxxxxxxxxxxxxmqgr0d'

class AllBlocksMonitor:
    def __init__(self):
        self.ws = None
        self.bridge_tx_count = 0
        self.total_tx_count = 0
        
    async def connect(self):
        """Connect to WebSocket and subscribe to all account blocks."""
        print(f"🔌 Connecting to {WSS_URL}...")
        
        try:
            self.ws = await websockets.connect(WSS_URL)
            print("✅ Connected to WebSocket")
            
            # Subscribe to all account blocks
            subscribe_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "ledger.subscribe",
                "params": ["allAccountBlocks"]
            }
            
            print(f"📤 Sending subscription: {json.dumps(subscribe_msg, indent=2)}")
            await self.ws.send(json.dumps(subscribe_msg))
            
            # Wait for subscription confirmation
            response = await self.ws.recv()
            response_data = json.loads(response)
            print(f"📥 Subscription response: {json.dumps(response_data, indent=2)}")
            
            if 'result' in response_data:
                print(f"✅ Subscribed successfully! Subscription ID: {response_data['result']}")
            else:
                print(f"❌ Subscription failed: {response_data}")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            raise
    
    async def listen(self):
        """Listen for account blocks and analyze them."""
        print("\n👂 Listening for account blocks...")
        print("=" * 80)
        
        try:
            while True:
                message = await self.ws.recv()
                data = json.loads(message)
                
                if 'method' in data and data['method'] == 'ledger.subscription':
                    await self.process_block(data)
                    
        except websockets.exceptions.ConnectionClosed:
            print("❌ WebSocket connection closed")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def process_block(self, data):
        """Process and analyze account block data."""
        self.total_tx_count += 1
        
        try:
            # Extract block data
            params = data.get('params', {})
            result = params.get('result', [])
            
            if result and len(result) > 0:
                block = result[0]
                
                # Check if it's related to the bridge
                to_address = block.get('toAddress', '')
                from_address = block.get('address', '')
                
                is_bridge_tx = (to_address == BRIDGE_ADDRESS or from_address == BRIDGE_ADDRESS)
                
                if is_bridge_tx:
                    self.bridge_tx_count += 1
                    print(f"\n🌉 BRIDGE TRANSACTION #{self.bridge_tx_count}")
                    print("=" * 80)
                    self.print_block_details(block)
                    
                    # Save to file for analysis
                    filename = f"bridge_tx_{self.bridge_tx_count}_{block.get('hash', 'unknown')[:8]}.json"
                    with open(filename, 'w') as f:
                        json.dump(block, f, indent=2)
                    print(f"💾 Saved to {filename}")
                    
                else:
                    # Show summary for non-bridge transactions
                    if self.total_tx_count % 100 == 0:
                        print(f"📊 Processed {self.total_tx_count} blocks total, {self.bridge_tx_count} bridge transactions")
                        
        except Exception as e:
            print(f"❌ Error processing block: {e}")
            print(f"Raw data: {json.dumps(data, indent=2)}")
    
    def print_block_details(self, block):
        """Print detailed block information."""
        print(f"Hash: {block.get('hash', 'N/A')}")
        print(f"Type: {block.get('blockType', 'N/A')}")
        print(f"From: {block.get('address', 'N/A')}")
        print(f"To: {block.get('toAddress', 'N/A')}")
        print(f"Token: {block.get('tokenStandard', 'N/A')}")
        print(f"Amount: {block.get('amount', 'N/A')}")
        print(f"Height: {block.get('height', 'N/A')}")
        
        # Check for data field
        if 'data' in block and block['data']:
            print(f"\n📦 Data field present:")
            print(f"  Length: {len(block['data'])} chars")
            print(f"  Preview: {block['data'][:100]}...")
            
        # Show all fields for debugging
        print(f"\n🔍 All fields in block:")
        for key, value in block.items():
            if key not in ['hash', 'blockType', 'address', 'toAddress', 'tokenStandard', 'amount', 'height', 'data']:
                if isinstance(value, (dict, list)):
                    print(f"  {key}: {json.dumps(value)[:100]}...")
                else:
                    print(f"  {key}: {value}")
        
        print("=" * 80)
    
    async def run(self):
        """Main run loop."""
        await self.connect()
        await self.listen()

async def main():
    """Main function."""
    print("🚀 Zenon Bridge Block Monitor")
    print(f"🌉 Bridge Address: {BRIDGE_ADDRESS}")
    print(f"🔗 WebSocket URL: {WSS_URL}")
    print("-" * 80)
    
    monitor = AllBlocksMonitor()
    
    try:
        await monitor.run()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        print(f"📊 Final stats: {monitor.total_tx_count} total blocks, {monitor.bridge_tx_count} bridge transactions")
        if monitor.ws:
            await monitor.ws.close()

if __name__ == "__main__":
    asyncio.run(main())