#!/usr/bin/env python3
"""
Database Viewer for Zenon Bridge Alert Bot
View contents of the bridge_bot.db database
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import sys

def view_database(db_path='data/bridge_bot.db'):
    """View all tables in the database."""
    
    # Check if database exists
    if not Path(db_path).exists():
        print(f"❌ Database not found at: {db_path}")
        print("Make sure the bot has run at least once to create the database.")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print(f"📊 Zenon Bridge Bot Database: {db_path}")
        print("=" * 80)
        
        # View Subscribers
        print("\n📱 SUBSCRIBERS:")
        print("-" * 80)
        cursor.execute("SELECT * FROM subscribers ORDER BY created_at DESC")
        subscribers = cursor.fetchall()
        
        if subscribers:
            print(f"{'User ID':<15} {'Username':<20} {'Active':<8} {'Filters':<30} {'Created At'}")
            print("-" * 80)
            for sub in subscribers:
                filters = json.loads(sub['filters']) if sub['filters'] else []
                filter_str = ', '.join(filters) if filters else 'All'
                active = '✅' if sub['active'] else '❌'
                username = sub['username'] or 'N/A'
                created = sub['created_at'][:19] if sub['created_at'] else 'N/A'
                
                print(f"{sub['user_id']:<15} {username:<20} {active:<8} {filter_str:<30} {created}")
        else:
            print("No subscribers found.")
        
        # View Recent Transactions
        print("\n💸 RECENT TRANSACTIONS (Last 20):")
        print("-" * 80)
        cursor.execute("""
            SELECT * FROM transactions 
            ORDER BY timestamp DESC 
            LIMIT 20
        """)
        transactions = cursor.fetchall()
        
        if transactions:
            for tx in transactions:
                print(f"\n🔹 {tx['type']} - {tx['hash'][:10]}...{tx['hash'][-8:]}")
                if tx['amount'] and tx['token']:
                    # Format amount with proper decimals
                    amount = float(tx['amount']) / 1e8 if tx['amount'] else 0
                    print(f"   Amount: {amount:,.2f} {tx['token']}")
                if tx['from_addr']:
                    print(f"   From: {tx['from_addr'][:10]}...{tx['from_addr'][-8:]}")
                if tx['to_addr']:
                    print(f"   To: {tx['to_addr'][:10]}...{tx['to_addr'][-8:]}")
                if tx['eth_addr']:
                    print(f"   ETH: {tx['eth_addr'][:10]}...{tx['eth_addr'][-8:]}")
                if tx['timestamp']:
                    print(f"   Time: {tx['timestamp']}")
        else:
            print("No transactions found.")
        
        # View Statistics Summary
        print("\n📈 TRANSACTION STATISTICS:")
        print("-" * 80)
        
        # Overall stats
        cursor.execute("SELECT COUNT(*) as total FROM transactions")
        total_tx = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM transactions 
            GROUP BY type 
            ORDER BY count DESC
        """)
        type_stats = cursor.fetchall()
        
        print(f"Total Transactions: {total_tx}")
        print("\nBy Type:")
        for stat in type_stats:
            print(f"  {stat['type']}: {stat['count']}")
        
        # Token volumes
        cursor.execute("""
            SELECT token, 
                   COUNT(*) as tx_count,
                   SUM(CAST(amount AS REAL))/100000000 as total_volume
            FROM transactions 
            WHERE token IS NOT NULL AND amount IS NOT NULL
            GROUP BY token
        """)
        token_stats = cursor.fetchall()
        
        if token_stats:
            print("\nBy Token:")
            for stat in token_stats:
                print(f"  {stat['token']}: {stat['tx_count']} transactions, {stat['total_volume']:,.2f} total volume")
        
        # Time-based stats
        print("\n📅 ACTIVITY BY PERIOD:")
        print("-" * 80)
        
        periods = [
            ("Last 24 hours", 1),
            ("Last 7 days", 7),
            ("Last 30 days", 30)
        ]
        
        for period_name, days in periods:
            cursor.execute(f"""
                SELECT COUNT(*) as count 
                FROM transactions 
                WHERE timestamp > datetime('now', '-{days} days')
            """)
            count = cursor.fetchone()['count']
            print(f"{period_name}: {count} transactions")
        
        conn.close()
        print("\n" + "=" * 80)
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def export_to_csv(db_path='data/bridge_bot.db', output_dir='exports'):
    """Export database tables to CSV files."""
    import csv
    from pathlib import Path
    
    Path(output_dir).mkdir(exist_ok=True)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Export each table
        tables = ['subscribers', 'transactions', 'statistics']
        
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            if rows:
                output_file = f"{output_dir}/{table}.csv"
                with open(output_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Write headers
                    writer.writerow(rows[0].keys())
                    # Write data
                    for row in rows:
                        writer.writerow(row)
                print(f"✅ Exported {table} to {output_file}")
            else:
                print(f"⚠️  No data in {table}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Export error: {e}")

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'export':
            print("Exporting database to CSV files...")
            export_to_csv()
        else:
            # Use provided database path
            view_database(sys.argv[1])
    else:
        # Use default path
        view_database()