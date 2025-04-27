# db/database.py
import sqlite3
import os
from config import DATABASE_PATH

class DatabaseManager:
    def __init__(self):
        """Initialize database connection"""
        self.conn = None
        self.cursor = None
        self.connect()
        
    def connect(self):
        """Connect to SQLite database"""
        try:
            self.conn = sqlite3.connect(DATABASE_PATH)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            self.cursor = self.conn.cursor()
            self.create_tables()
            return True
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            return False
    
    def create_tables(self):
        """Create necessary database tables if they don't exist"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS fines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fine_number TEXT UNIQUE,
            issue_date DATE,
            due_date DATE,
            amount REAL,
            violation_type TEXT,
            license_plate TEXT,
            driver_id_due_date DATE,
            description TEXT,
            violation_location TEXT,
            violation_time TEXT,
            person_name TEXT,
            equipment_number TEXT,
            agent_id TEXT,
            pdf_path TEXT,
            payment_event_created BOOLEAN DEFAULT 0,
            driver_id_event_created BOOLEAN DEFAULT 0
        )
        ''')
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Destructor to ensure database connection is closed"""
        self.close()