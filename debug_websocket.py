#!/usr/bin/env python3
"""
Debug WebSocket responses to understand data structure
"""

import asyncio
import websockets
import json
from datetime import datetime

WSS_URL = 'wss://my.hc1node.com:35998'
BRIDGE_ADDRESS = 'z1qxemdeddedxdrydgexxxxxxxxxxxxxxxmqgr0d'

async def test_subscription_methods():
    """Test different subscription methods and log responses."""
    
    print("🔍 Testing WebSocket subscription methods...")
    print("=" * 80)
    
    # Test 1: accountBlocksByAddress
    print("\n1️⃣ Testing accountBlocksByAddress...")
    try:
        ws = await websockets.connect(WSS_URL)
        
        # Subscribe
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "ledger.subscribe",
            "params": ["accountBlocksByAddress", BRIDGE_ADDRESS]
        }
        
        await ws.send(json.dumps(msg))
        response = await ws.recv()
        print(f"Response: {response}")
        
        # Wait for a notification
        print("Waiting for a notification (10 seconds)...")
        try:
            notification = await asyncio.wait_for(ws.recv(), timeout=10)
            print(f"Notification structure:")
            print(json.dumps(json.loads(notification), indent=2))
            
            # Analyze the structure
            data = json.loads(notification)
            if 'params' in data and 'result' in data['params']:
                result = data['params']['result']
                print(f"\nType of result: {type(result)}")
                if isinstance(result, list):
                    print(f"Result is a list with {len(result)} items")
                    if result:
                        print(f"First item type: {type(result[0])}")
                        print(f"First item keys: {list(result[0].keys()) if isinstance(result[0], dict) else 'Not a dict'}")
                        
        except asyncio.TimeoutError:
            print("No notifications received in 10 seconds")
            
        await ws.close()
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Check recent blocks manually
    print("\n2️⃣ Getting recent account blocks...")
    try:
        ws = await websockets.connect(WSS_URL)
        
        # Get account blocks by height
        msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "ledger.getAccountBlocksByHeight",
            "params": [BRIDGE_ADDRESS, 1, 5]  # Get last 5 blocks
        }
        
        await ws.send(json.dumps(msg))
        response = await ws.recv()
        data = json.loads(response)
        
        if 'result' in data and 'list' in data['result']:
            blocks = data['result']['list']
            print(f"Found {len(blocks)} recent blocks")
            
            for i, block in enumerate(blocks):
                print(f"\nBlock {i+1}:")
                print(f"  Hash: {block.get('hash', 'N/A')}")
                print(f"  Type: {block.get('blockType', 'N/A')}")
                print(f"  From: {block.get('address', 'N/A')}")
                print(f"  To: {block.get('toAddress', 'N/A')}")
                print(f"  Token: {block.get('tokenStandard', 'N/A')}")
                print(f"  Amount: {block.get('amount', 'N/A')}")
                print(f"  Data present: {'Yes' if block.get('data') else 'No'}")
                
                # Save a sample
                if i == 0 and block.get('data'):
                    with open('sample_bridge_block.json', 'w') as f:
                        json.dump(block, f, indent=2)
                    print(f"  💾 Saved to sample_bridge_block.json")
                    
        await ws.close()
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 80)
    print("✅ Debug complete!")

if __name__ == "__main__":
    asyncio.run(test_subscription_methods())