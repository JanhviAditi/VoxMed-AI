# utils/validators.py – Input validation helpers for VoxMed AI
import re
from datetime import datetime, date


def validate_name(name: str) -> tuple:
    """Validates a patient or doctor name. Returns (is_valid, error_message)"""
    name = name.strip()
    if not name:
        return False, "Name cannot be empty."
    if len(name) < 2:
        return False, "Name is too short."
    if re.search(r'[0-9@#$%^&*()_+=\[\]{};\'\\:"|,.<>?/]', name):
        return False, "Name should only contain letters and spaces."
    return True, ""


def validate_date(date_str: str) -> tuple:
    """Validates a date string in YYYY-MM-DD format. Returns (is_valid, error_message)"""
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return False, f"Invalid date format: '{date_str}'. Use YYYY-MM-DD."
    if parsed < date.today():
        return False, "Appointment date cannot be in the past."
    return True, ""


def validate_time(time_str: str) -> tuple:
    """Validates a time string in HH:MM format. Returns (is_valid, error_message)"""
    try:
        parsed = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return False, f"Invalid time format: '{time_str}'. Use HH:MM (e.g. 14:30)."
    clinic_open  = datetime.strptime("09:00", "%H:%M").time()
    clinic_close = datetime.strptime("18:00", "%H:%M").time()
    if not (clinic_open <= parsed <= clinic_close):
        return False, "Appointment time must be between 09:00 and 18:00."
    return True, ""


def validate_phone(phone: str) -> tuple:
    """Validates an Indian mobile number. Returns (is_valid, error_message)"""
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+91"):
        phone = phone[3:]
    if phone.startswith("91") and len(phone) == 12:
        phone = phone[2:]
    if not re.fullmatch(r'[6-9]\d{9}', phone):
        return False, f"Invalid phone: '{phone}'. Must be a 10-digit Indian mobile number."
    return True, ""
