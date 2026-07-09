"""
services/appointments.py
------------------------
Business logic for managing appointments.
"""
from typing import Optional
from database import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)

def _get_or_create_patient(name: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM patients WHERE name = ? COLLATE NOCASE", (name,))
    row = cursor.fetchone()
    
    if row:
        patient_id = row['id']
    else:
        cursor.execute("INSERT INTO patients (name) VALUES (?)", (name,))
        conn.commit()
        patient_id = cursor.lastrowid
        logger.info("Created new patient: %s (id: %d)", name, patient_id)
        
    conn.close()
    return patient_id

def book_appointment(name: str, doctor: str, date: str, time: str) -> tuple[bool, str]:
    """Books an appointment for the given patient."""
    patient_id = _get_or_create_patient(name)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Simple conflict check for same patient on same date
    cursor.execute('''
        SELECT id FROM appointments 
        WHERE patient_id = ? AND appointment_date = ? AND status = 'BOOKED'
    ''', (patient_id, date))
    
    if cursor.fetchone():
        conn.close()
        return False, f"You already have a booked appointment on {date}."

    cursor.execute('''
        INSERT INTO appointments (patient_id, doctor, appointment_date, appointment_time, status)
        VALUES (?, ?, ?, ?, 'BOOKED')
    ''', (patient_id, doctor, date, time))
    
    conn.commit()
    conn.close()
    
    logger.info("Appointment booked for %s with %s on %s at %s", name, doctor, date, time)
    return True, f"Great! Your appointment with {doctor} on {date} at {time} has been booked."

def cancel_appointment(name: str, date: str) -> tuple[bool, str]:
    """Cancels an appointment for the given patient on a specific date."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM patients WHERE name = ? COLLATE NOCASE", (name,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False, f"Sorry, I couldn't find a patient record for {name}."
        
    patient_id = row['id']
    
    cursor.execute('''
        SELECT id FROM appointments 
        WHERE patient_id = ? AND appointment_date = ? AND status = 'BOOKED'
    ''', (patient_id, date))
    
    appt = cursor.fetchone()
    if not appt:
        conn.close()
        return False, f"Sorry, I couldn't find a booked appointment on {date} for {name}."
        
    cursor.execute('''
        UPDATE appointments SET status = 'CANCELED' WHERE id = ?
    ''', (appt['id'],))
    
    conn.commit()
    conn.close()
    
    logger.info("Appointment canceled for %s on %s", name, date)
    return True, f"Your appointment on {date} has been successfully canceled."

def reschedule_appointment(name: str, date: str, time: str) -> tuple[bool, str]:
    """
    Reschedules an appointment. For simplicity, we find the first BOOKED appointment 
    for this patient, mark it RESCHEDULED, and create a new one.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM patients WHERE name = ? COLLATE NOCASE", (name,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False, f"Sorry, I couldn't find a patient record for {name}."
        
    patient_id = row['id']
    
    # Find any active appointment
    cursor.execute('''
        SELECT id, doctor FROM appointments 
        WHERE patient_id = ? AND status = 'BOOKED'
        ORDER BY appointment_date ASC LIMIT 1
    ''', (patient_id,))
    
    appt = cursor.fetchone()
    if not appt:
        conn.close()
        return False, f"Sorry, I couldn't find any active appointments for {name} to reschedule."
        
    # Mark old as RESCHEDULED
    cursor.execute('''
        UPDATE appointments SET status = 'RESCHEDULED' WHERE id = ?
    ''', (appt['id'],))
    
    # Insert new
    cursor.execute('''
        INSERT INTO appointments (patient_id, doctor, appointment_date, appointment_time, status)
        VALUES (?, ?, ?, ?, 'BOOKED')
    ''', (patient_id, appt['doctor'], date, time))
    
    conn.commit()
    conn.close()
    
    logger.info("Appointment rescheduled for %s to %s at %s", name, date, time)
    return True, f"Your appointment has been successfully rescheduled to {date} at {time}."

def check_availability(date: str) -> tuple[bool, str]:
    """Checks how many appointments exist on a given date."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(id) as count FROM appointments 
        WHERE appointment_date = ? AND status = 'BOOKED'
    ''', (date,))
    
    count = cursor.fetchone()['count']
    conn.close()
    
    if count < 10:  # Arbitrary limit for mock logic
        return True, f"Yes, there are slots available on {date}. We have {count} appointments booked so far."
    else:
        return False, f"Sorry, {date} is fully booked. Would you like to check another day?"
