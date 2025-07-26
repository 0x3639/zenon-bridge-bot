#!/usr/bin/env python3
"""
Simple Database Viewer - No dependencies except sqlite3
"""

import sqlite3
import json

def view_database(db_path='data/bridge_bot.db'):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n=== SUBSCRIBERS ===")
        cursor.execute("SELECT user_id, username, active, filters FROM subscribers")
        for row in cursor.fetchall():
            active = 'Active' if row[2] else 'Inactive'
            print(f"User: {row[0]} ({row[1] or 'No username'}) - {active}")
            if row[3]:
                filters = json.loads(row[3])
                if filters:
                    print(f"  Filters: {', '.join(filters)}")
        
        print("\n=== RECENT TRANSACTIONS (Last 10) ===")
        cursor.execute("""
            SELECT type, hash, amount, token, timestamp 
            FROM transactions 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1][:16]}...")
            if row[2] and row[3]:
                amount = float(row[2]) / 1e8
                print(f"  {amount:,.2f} {row[3]} at {row[4]}")
        
        print("\n=== SUMMARY ===")
        cursor.execute("SELECT COUNT(*) FROM transactions")
        total = cursor.fetchone()[0]
        print(f"Total transactions: {total}")
        
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM subscribers WHERE active=1")
        subs = cursor.fetchone()[0]
        print(f"Active subscribers: {subs}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    view_database()