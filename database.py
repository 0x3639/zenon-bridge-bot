import aiosqlite
import json
import asyncio
from pathlib import Path
from src.config import DATABASE_PATH

async def init_database():
    """Initialize the SQLite database with required tables."""
    # Ensure the directory exists
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
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
        print(f"Database initialized at {DATABASE_PATH}")

class Database:
    def __init__(self):
        self.path = DATABASE_PATH
    
    async def add_subscriber(self, user_id, username=None):
        """Add a new subscriber to the database."""
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO subscribers (user_id, username, active) VALUES (?, ?, 1)",
                (user_id, username)
            )
            await db.commit()
    
    async def remove_subscriber(self, user_id):
        """Mark a subscriber as inactive."""
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE subscribers SET active = 0 WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()
    
    async def get_active_subscribers(self):
        """Get all active subscribers."""
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                "SELECT user_id, username, filters FROM subscribers WHERE active = 1"
            ) as cursor:
                subscribers = []
                async for row in cursor:
                    user_filters = json.loads(row[2]) if row[2] else []
                    
                    # Clean up any invalid filters (safety check)
                    valid_filters = ['WrapToken', 'UnwrapToken', 'Redeem']
                    cleaned_filters = [f for f in user_filters if f in valid_filters]
                    
                    # If filters were cleaned, update the database
                    if len(cleaned_filters) != len(user_filters):
                        await db.execute(
                            "UPDATE subscribers SET filters = ? WHERE user_id = ?",
                            (json.dumps(cleaned_filters), row[0])
                        )
                        await db.commit()
                        print(f"Cleaned invalid filters for user {row[0]}")
                    
                    subscribers.append({
                        'user_id': row[0],
                        'username': row[1],
                        'filters': cleaned_filters
                    })
                return subscribers
    
    async def update_subscriber_filters(self, user_id, filters):
        """Update subscriber's transaction type filters."""
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE subscribers SET filters = ? WHERE user_id = ?",
                (json.dumps(filters), user_id)
            )
            await db.commit()
    
    async def add_transaction(self, tx_data):
        """Add a transaction to the database."""
        async with aiosqlite.connect(self.path) as db:
            # Convert datetime to string if present
            timestamp = tx_data.get('timestamp')
            if timestamp and hasattr(timestamp, 'isoformat'):
                timestamp = timestamp.isoformat()
            
            try:
                await db.execute("""
                    INSERT OR IGNORE INTO transactions 
                    (hash, type, amount, token, from_addr, to_addr, eth_addr, timestamp, block_height)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tx_data.get('hash'),
                    tx_data.get('type'),
                    tx_data.get('amount'),
                    tx_data.get('token'),
                    tx_data.get('from_addr'),
                    tx_data.get('to_addr'),
                    tx_data.get('eth_addr'),
                    timestamp,
                    tx_data.get('block_height')
                ))
                await db.commit()
                print(f"Transaction saved: {tx_data.get('type')} - {tx_data.get('hash', '')[:16]}...")
            except Exception as e:
                print(f"Error saving transaction: {e}")
                print(f"Transaction data: {tx_data}")
    
    async def get_statistics(self, period_days=1):
        """Get transaction statistics for a given period."""
        async with aiosqlite.connect(self.path) as db:
            # First, let's check if we have any transactions at all
            async with db.execute("SELECT COUNT(*) FROM transactions") as cursor:
                total = await cursor.fetchone()
                print(f"Total transactions in database: {total[0]}")
            
            query = """
                SELECT 
                    type, 
                    COUNT(*) as count, 
                    token,
                    SUM(CAST(amount AS REAL)) as volume
                FROM transactions 
                WHERE timestamp IS NULL OR timestamp > datetime('now', '-{} days')
                GROUP BY type, token
            """.format(period_days)
            
            async with db.execute(query) as cursor:
                stats = []
                async for row in cursor:
                    stats.append({
                        'type': row[0],
                        'count': row[1],
                        'token': row[2],
                        'volume': row[3]
                    })
                
                if not stats:
                    print(f"No stats found for period: {period_days} days")
                else:
                    print(f"Found {len(stats)} stat entries")
                    
                return stats

if __name__ == "__main__":
    # Initialize database when script is run directly
    asyncio.run(init_database())