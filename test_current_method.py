#!/usr/bin/env python3
"""
Test the current subscription method (accountBlocksByAddress) 
"""

import asyncio
import websockets
import json
from datetime import datetime

# Configuration
WSS_URL = 'wss://my.hc1node.com:35998'
BRIDGE_ADDRESS = 'z1qxemdeddedxdrydgexxxxxxxxxxxxxxxmqgr0d'

class CurrentMethodMonitor:
    def __init__(self):
        self.ws = None
        self.tx_count = 0
        
    async def connect(self):
        """Connect using the current method."""
        print(f"🔌 Connecting to {WSS_URL}...")
        
        try:
            self.ws = await websockets.connect(WSS_URL)
            print("✅ Connected to WebSocket")
            
            # Subscribe using current method
            subscribe_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "ledger.subscribe",
                "params": ["accountBlocksByAddress", BRIDGE_ADDRESS]
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
        """Listen for blocks."""
        print("\n👂 Listening for bridge account blocks...")
        print("=" * 80)
        
        try:
            while True:
                message = await self.ws.recv()
                data = json.loads(message)
                
                if 'method' in data and data['method'] == 'ledger.subscription':
                    self.tx_count += 1
                    print(f"\n📦 RECEIVED BLOCK #{self.tx_count} at {datetime.now()}")
                    print("=" * 80)
                    print(json.dumps(data, indent=2))
                    
                    # Save for comparison
                    filename = f"current_method_tx_{self.tx_count}.json"
                    with open(filename, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"💾 Saved to {filename}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("❌ WebSocket connection closed")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def run(self):
        """Main run loop."""
        await self.connect()
        await self.listen()

async def main():
    """Main function."""
    print("🚀 Current Method Test (accountBlocksByAddress)")
    print(f"🌉 Bridge Address: {BRIDGE_ADDRESS}")
    print(f"🔗 WebSocket URL: {WSS_URL}")
    print("-" * 80)
    
    monitor = CurrentMethodMonitor()
    
    try:
        await monitor.run()
    except KeyboardInterrupt:
        print(f"\n\n👋 Shutting down... Received {monitor.tx_count} blocks")
        if monitor.ws:
            await monitor.ws.close()

if __name__ == "__main__":
    asyncio.run(main())