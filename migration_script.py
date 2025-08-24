#!/usr/bin/env python3
"""
Database migration script for Bridge Bot v2.0

This script:
1. Ensures all required tables exist 
2. Cleans up invalid filters from existing users
3. Safely migrates production database without losing user data
"""

import asyncio
import aiosqlite
import json
import os
from pathlib import Path

# Get database path from environment or use default
DATABASE_PATH = os.getenv('DATABASE_PATH', './data/bridge_bot.db')

async def migrate_database():
    """Migrate the database schema and clean up invalid data."""
    
    print("🚀 Starting Bridge Bot Database Migration")
    print("=" * 60)
    
    # Ensure data directory exists
    data_dir = Path(DATABASE_PATH).parent
    data_dir.mkdir(exist_ok=True)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        
        # 1. Check current schema
        print("📋 Checking current database schema...")
        
        # Check if tables exist
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
            tables = [row[0] async for row in cursor]
            print(f"   Found tables: {', '.join(tables) if tables else 'None'}")
        
        # 2. Create missing tables (this is safe - CREATE TABLE IF NOT EXISTS)
        print("\n🔧 Ensuring all required tables exist...")
        
        # Create subscribers table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                active BOOLEAN DEFAULT 1,
                filters TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create transactions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                hash TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                amount TEXT,
                token TEXT,
                from_addr TEXT,
                to_addr TEXT,
                eth_addr TEXT,
                timestamp TIMESTAMP,
                block_height INTEGER
            )
        """)
        
        # Create statistics table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                date DATE PRIMARY KEY,
                tx_count INTEGER DEFAULT 0,
                volume_by_token TEXT DEFAULT '{}'
            )
        """)
        
        await db.commit()
        print("   ✅ All tables created/verified")
        
        # 3. Check current users and their filters
        print("\n👥 Analyzing existing users and filters...")
        
        async with db.execute("SELECT COUNT(*) FROM subscribers") as cursor:
            total_users = (await cursor.fetchone())[0]
            
        print(f"   Total users: {total_users}")
        
        users_updated = 0  # Initialize here to avoid scope issues
        
        if total_users == 0:
            print("   📝 No existing users found - this is a fresh installation")
        else:
            # 4. Clean up invalid filters
            print("\n🧹 Cleaning up invalid transaction type filters...")
            
            # Valid filters in new version (only these 3)
            VALID_FILTERS = ['WrapToken', 'UnwrapToken', 'Redeem']
            
            # Old filters that are no longer supported
            OLD_FILTERS = ['Transfer', 'UpdateWrapRequest']
            
            async with db.execute("SELECT user_id, username, filters FROM subscribers WHERE active = 1") as cursor:
                async for row in cursor:
                    user_id, username, filters_json = row
                    
                    if filters_json:
                        try:
                            current_filters = json.loads(filters_json)
                            
                            # Clean filters - remove invalid ones
                            new_filters = [f for f in current_filters if f in VALID_FILTERS]
                            
                            # Check if we removed any filters
                            removed_filters = [f for f in current_filters if f not in VALID_FILTERS]
                            
                            if removed_filters:
                                print(f"   👤 User {user_id} ({username}): Removing invalid filters: {removed_filters}")
                                
                                # Update user's filters
                                await db.execute(
                                    "UPDATE subscribers SET filters = ? WHERE user_id = ?",
                                    (json.dumps(new_filters), user_id)
                                )
                                users_updated += 1
                        except json.JSONDecodeError:
                            print(f"   ⚠️  User {user_id} has invalid filter JSON, clearing...")
                            await db.execute(
                                "UPDATE subscribers SET filters = '[]' WHERE user_id = ?",
                                (user_id,)
                            )
                            users_updated += 1
            
            await db.commit()
            
            if users_updated > 0:
                print(f"   ✅ Updated filters for {users_updated} users")
            else:
                print("   ✅ All user filters are already valid")
        
        # 5. Check existing transactions
        print("\n📊 Checking transaction data...")
        
        async with db.execute("SELECT COUNT(*) FROM transactions") as cursor:
            total_txs = (await cursor.fetchone())[0]
            
        print(f"   Total transactions: {total_txs}")
        
        if total_txs > 0:
            # Show transaction type breakdown
            async with db.execute("SELECT type, COUNT(*) FROM transactions GROUP BY type") as cursor:
                tx_types = {row[0]: row[1] async for row in cursor}
                print("   Transaction types:")
                for tx_type, count in tx_types.items():
                    print(f"     - {tx_type}: {count}")
        
        print("\n🎉 Migration completed successfully!")
        print("=" * 60)
        
        print("\n📋 Summary:")
        print(f"   • Total users preserved: {total_users}")
        print(f"   • Users with updated filters: {users_updated}")
        print(f"   • Transaction history preserved: {total_txs} transactions")
        print("\n✅ Your production bot is ready to run with the new version!")
        
        return total_users, users_updated, total_txs

async def verify_migration():
    """Verify the migration was successful."""
    print("\n🔍 Verifying migration...")
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Check that all users have valid filters only
        async with db.execute("""
            SELECT user_id, username, filters 
            FROM subscribers 
            WHERE active = 1 AND filters != '[]'
        """) as cursor:
            
            invalid_found = False
            VALID_FILTERS = ['WrapToken', 'UnwrapToken', 'Redeem']
            
            async for row in cursor:
                user_id, username, filters_json = row
                filters = json.loads(filters_json)
                
                invalid_filters = [f for f in filters if f not in VALID_FILTERS]
                if invalid_filters:
                    print(f"   ❌ User {user_id} still has invalid filters: {invalid_filters}")
                    invalid_found = True
            
            if not invalid_found:
                print("   ✅ All user filters are valid")
                return True
            else:
                print("   ❌ Some users still have invalid filters")
                return False

if __name__ == "__main__":
    async def run_migration():
        try:
            total_users, users_updated, total_txs = await migrate_database()
            success = await verify_migration()
            
            if success:
                print("\n🎉 Migration completed successfully!")
                return True
            else:
                print("\n❌ Migration verification failed")
                return False
                
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    success = asyncio.run(run_migration())
    exit(0 if success else 1)