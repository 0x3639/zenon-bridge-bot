#!/usr/bin/env python3
"""
View logs and WebSocket data for debugging
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def view_recent_logs():
    """View recent log files."""
    logs_dir = Path('logs')
    
    if not logs_dir.exists():
        print("❌ Logs directory not found. Run the bot first to generate logs.")
        return
    
    print("📁 Log Files:")
    print("=" * 80)
    
    # Show bot log
    bot_log = logs_dir / 'bot.log'
    if bot_log.exists():
        print(f"📄 Bot Log (last 20 lines):")
        with open(bot_log, 'r') as f:
            lines = f.readlines()
            for line in lines[-20:]:
                print(f"  {line.strip()}")
        print("-" * 80)
    
    # Show WebSocket files
    ws_files = sorted(logs_dir.glob('ws_*.json'), key=lambda x: x.stat().st_mtime, reverse=True)
    print(f"📡 WebSocket Messages ({len(ws_files)} files):")
    
    for i, file in enumerate(ws_files[:5]):  # Show last 5
        print(f"  {i+1}. {file.name} ({file.stat().st_size} bytes)")
        
        if len(sys.argv) > 1 and sys.argv[1] == 'detailed':
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    print(f"     Method: {data.get('method', 'N/A')}")
                    if 'params' in data:
                        result = data['params'].get('result', [])
                        if isinstance(result, list):
                            print(f"     Blocks: {len(result)}")
                        else:
                            print(f"     Result: {type(result).__name__}")
            except:
                print(f"     Error reading file")
        
    print("-" * 80)
    
    # Show transaction files
    tx_files = sorted(logs_dir.glob('tx_*.json'), key=lambda x: x.stat().st_mtime, reverse=True)
    print(f"💸 Decoded Transactions ({len(tx_files)} files):")
    
    for i, file in enumerate(tx_files[:10]):  # Show last 10
        try:
            with open(file, 'r') as f:
                tx = json.load(f)
                direction = "TO" if "to_bridge" in file.name else "FROM"
                print(f"  {i+1}. {direction} bridge: {tx.get('type', 'Unknown')} - {tx.get('hash', 'N/A')[:16]}...")
                if tx.get('eth_addr'):
                    print(f"     ETH: {tx['eth_addr']}")
        except:
            print(f"  {i+1}. {file.name} (error reading)")

def view_specific_file(filename):
    """View a specific log file."""
    logs_dir = Path('logs')
    file_path = logs_dir / filename
    
    if not file_path.exists():
        print(f"❌ File not found: {filename}")
        return
    
    try:
        with open(file_path, 'r') as f:
            if filename.endswith('.json'):
                data = json.load(f)
                print(json.dumps(data, indent=2))
            else:
                print(f.read())
    except Exception as e:
        print(f"❌ Error reading file: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and not sys.argv[1] == 'detailed':
        view_specific_file(sys.argv[1])
    else:
        view_recent_logs()
        print("\nUsage:")
        print("  python3 view_logs.py                  # Show recent logs summary")
        print("  python3 view_logs.py detailed        # Show detailed WebSocket info")
        print("  python3 view_logs.py filename.json   # View specific file")