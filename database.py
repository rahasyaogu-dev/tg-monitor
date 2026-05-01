import sqlite3
import json

# SQLite setup - uses local file, no URL needed
class Database:
    def __init__(self, db_path="instagram_monitor.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Create tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    time_interval INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Monitors table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monitors (
                    monitor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    type TEXT NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    profile_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # Channel config table - SIMPLIFIED VERSION
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channel_config (
                    user_id TEXT PRIMARY KEY,
                    ban_channel TEXT,
                    unban_channel TEXT,
                    verify_channel TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_active 
                ON monitors(user_id, active)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_channel_user 
                ON channel_config(user_id)
            """)
            
            conn.commit()

# Initialize database
db = Database()

def get_user(user_id):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, time_interval FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return {"user_id": row[0], "time_interval": row[1]}
        return None

def set_user_time(user_id, time_minutes):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, time_interval, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET 
                time_interval = excluded.time_interval,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, time_minutes))
        conn.commit()

def get_user_time(user_id):
    user = get_user(user_id)
    return user.get("time_interval") if user else None

def add_monitor(user_id, username, monitor_type, profile_data):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO monitors (user_id, username, type, active, profile_data)
            VALUES (?, ?, ?, 1, ?)
        """, (user_id, username, monitor_type, json.dumps(profile_data)))
        conn.commit()
        return cursor.lastrowid

def get_active_monitors(user_id):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT monitor_id, user_id, username, type, active, profile_data
            FROM monitors 
            WHERE user_id = ? AND active = 1
        """, (user_id,))
        rows = cursor.fetchall()
        monitors = []
        for row in rows:
            monitors.append({
                "_id": row[0],
                "monitor_id": row[0],
                "user_id": row[1],
                "username": row[2],
                "type": row[3],
                "active": bool(row[4]),
                "profile_data": json.loads(row[5]) if row[5] else {}
            })
        return monitors

def stop_monitor(monitor_id):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE monitors 
            SET active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE monitor_id = ?
        """, (monitor_id,))
        conn.commit()

def delete_monitor(monitor_id):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM monitors WHERE monitor_id = ?", (monitor_id,))
        conn.commit()

def get_monitor_by_id(monitor_id):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT monitor_id, user_id, username, type, active, profile_data
            FROM monitors 
            WHERE monitor_id = ?
        """, (monitor_id,))
        row = cursor.fetchone()
        if row:
            return {
                "_id": row[0],
                "monitor_id": row[0],
                "user_id": row[1],
                "username": row[2],
                "type": row[3],
                "active": bool(row[4]),
                "profile_data": json.loads(row[5]) if row[5] else {}
            }
        return None

# UPDATED Channel configuration functions
def set_channel_config(user_id, channel_target, channel_type, value=None):
    """
    Set channel configuration for a user
    channel_type: "ban_channel", "unban_channel", or "verify_channel"
    channel_target: the channel ID or channel:topic format
    """
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if user exists in channel_config
        cursor.execute("SELECT user_id FROM channel_config WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone()
        
        if channel_type == "ban_channel":
            if exists:
                cursor.execute("""
                    UPDATE channel_config 
                    SET ban_channel = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (channel_target, user_id))
            else:
                cursor.execute("""
                    INSERT INTO channel_config (user_id, ban_channel, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (user_id, channel_target))
        
        elif channel_type == "unban_channel":
            if exists:
                cursor.execute("""
                    UPDATE channel_config 
                    SET unban_channel = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (channel_target, user_id))
            else:
                cursor.execute("""
                    INSERT INTO channel_config (user_id, unban_channel, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (user_id, channel_target))
        
        elif channel_type == "verify_channel":
            if exists:
                cursor.execute("""
                    UPDATE channel_config 
                    SET verify_channel = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (channel_target, user_id))
            else:
                cursor.execute("""
                    INSERT INTO channel_config (user_id, verify_channel, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (user_id, channel_target))
        
        conn.commit()
        print(f"✅ Saved {channel_type}: {channel_target} for user {user_id}")

def get_channel_config(user_id, channel_type=None):
    """
    Get channel configuration for a user
    If channel_type is provided, returns that specific channel
    Otherwise returns dict with all channels
    """
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ban_channel, unban_channel, verify_channel
            FROM channel_config 
            WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        
        if not row:
            return None if channel_type else {}
        
        if channel_type:
            if channel_type == "ban_channel":
                return row[0]
            elif channel_type == "unban_channel":
                return row[1]
            elif channel_type == "verify_channel":
                return row[2]
            return None
        
        return {
            "ban_channel": row[0],
            "unban_channel": row[1],
            "verify_channel": row[2]
        }

def get_notification_target(user_id, notification_type):
    """Get the target channel for a notification type (legacy function)"""
    if notification_type == "ban":
        return get_channel_config(user_id, "ban_channel")
    elif notification_type == "unban":
        return get_channel_config(user_id, "unban_channel")
    elif notification_type == "verify":
        return get_channel_config(user_id, "verify_channel")
    return None

def clear_channel_config(user_id):
    """Clear all channel configuration for a user"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM channel_config WHERE user_id = ?", (user_id,))
        conn.commit()
        print(f"✅ Cleared all channel config for user {user_id}")