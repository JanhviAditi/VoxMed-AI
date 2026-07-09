"""
database.py
-----------
SQLite database connection and schema initialization.
"""
import sqlite3
import config
from utils.logger import get_logger

logger = get_logger(__name__)

def get_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    if config.DB_ECHO:
        conn.set_trace_callback(print)
    return conn

def init_db():
    """Initializes the database schema if it doesn't exist."""
    logger.info("Initializing database schema at %s", config.DB_PATH)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create appointments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor TEXT,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT,
            status TEXT NOT NULL DEFAULT 'BOOKED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database schema initialized successfully.")

if __name__ == "__main__":
    init_db()
