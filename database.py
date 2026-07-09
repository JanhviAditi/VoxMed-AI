"""
database.py
-----------
SQLite database connection, schema initialization, and dummy data generation.
"""
import sqlite3
import config
from utils.logger import get_logger
from datetime import date, timedelta

logger = get_logger(__name__)

def get_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = 1")
    if config.DB_ECHO:
        conn.set_trace_callback(print)
    return conn

def init_db():
    """Initializes the 9-table database schema."""
    logger.info("Initializing database schema at %s", config.DB_PATH)
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Drop existing tables if they exist to start fresh with new schema
    tables = [
        "Feedback", "AI_Logs", "Conversations", "Calls", 
        "Appointments", "Slots", "Doctors", "Departments", "Patients"
    ]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    # 2. Create Tables
    cursor.executescript('''
        CREATE TABLE Departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE Doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES Departments (id)
        );

        CREATE TABLE Patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE Slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            slot_date TEXT NOT NULL,
            slot_time TEXT NOT NULL,
            is_booked BOOLEAN NOT NULL DEFAULT 0,
            FOREIGN KEY (doctor_id) REFERENCES Doctors (id),
            UNIQUE(doctor_id, slot_date, slot_time)
        );

        CREATE TABLE Appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            slot_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'BOOKED', -- BOOKED, CANCELED, RESCHEDULED, COMPLETED
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES Patients (id),
            FOREIGN KEY (doctor_id) REFERENCES Doctors (id),
            FOREIGN KEY (slot_id) REFERENCES Slots (id)
        );

        CREATE TABLE Calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'ONGOING', -- ONGOING, COMPLETED, DROPPED
            FOREIGN KEY (patient_id) REFERENCES Patients (id)
        );

        CREATE TABLE Conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id INTEGER NOT NULL,
            speaker TEXT NOT NULL, -- 'AI' or 'Patient'
            transcript TEXT NOT NULL,
            detected_intent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (call_id) REFERENCES Calls (id)
        );

        CREATE TABLE AI_Logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module TEXT NOT NULL, -- 'STT', 'NLP', 'TTS', 'DM'
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE Feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER NOT NULL,
            rating INTEGER,
            comments TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES Appointments (id)
        );
    ''')
    conn.commit()
    logger.info("Database schema initialized successfully.")

    # 3. Inject Dummy Data
    _inject_dummy_data(cursor)
    conn.commit()
    conn.close()

def _inject_dummy_data(cursor):
    logger.info("Injecting dummy data for testing...")
    
    # Insert Departments
    cursor.execute("INSERT INTO Departments (name) VALUES ('General Medicine')")
    gen_med_id = cursor.lastrowid
    cursor.execute("INSERT INTO Departments (name) VALUES ('Cardiology')")
    cardio_id = cursor.lastrowid

    # Insert Doctors
    cursor.execute("INSERT INTO Doctors (name, department_id) VALUES ('Dr. Sharma', ?)", (gen_med_id,))
    sharma_id = cursor.lastrowid
    cursor.execute("INSERT INTO Doctors (name, department_id) VALUES ('Dr. Gupta', ?)", (cardio_id,))
    gupta_id = cursor.lastrowid

    # Insert Slots for tomorrow and day after
    today = date.today()
    tomorrow = (today + timedelta(days=1)).isoformat()
    day_after = (today + timedelta(days=2)).isoformat()
    
    times = ["09:00", "10:00", "14:00", "15:00"]
    
    for d_id in [sharma_id, gupta_id]:
        for d_date in [tomorrow, day_after]:
            for t in times:
                cursor.execute(
                    "INSERT INTO Slots (doctor_id, slot_date, slot_time, is_booked) VALUES (?, ?, ?, 0)",
                    (d_id, d_date, t)
                )

if __name__ == "__main__":
    init_db()
