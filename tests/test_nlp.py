"""
tests/test_nlp.py
Run with:  python -m pytest tests/test_nlp.py -v
"""

import pytest
from datetime import date, timedelta
from processing.nlp import analyse


def intent(text):       return analyse(text)["intent"]
def entity(text, key):  return analyse(text)["entities"][key]
def missing(text):      return analyse(text)["missing_entities"]
def followup(text):     return analyse(text)["follow_up_question"]


# ── book_appointment ──────────────────────────────────────────────────────────

def test_book_basic():
    assert intent("I want to book an appointment with Dr. Sharma") == "book_appointment"

def test_book_schedule():
    assert intent("Can you schedule an appointment for me?") == "book_appointment"

def test_book_consult():
    assert intent("I need to consult a cardiologist") == "book_appointment"

def test_book_id_like():
    assert intent("I'd like an appointment with Dr. Rao") == "book_appointment"

def test_book_can_i_see():
    assert intent("Can I see Dr Sharma tomorrow?") == "book_appointment"

def test_book_want_to_meet():
    assert intent("I want to meet doctor Kapoor") == "book_appointment"

def test_book_hindi():
    assert intent("मुझे डॉक्टर से मिलना है, अपॉइंटमेंट लेना है") == "book_appointment"

def test_book_hindi_2():
    assert intent("कल के लिए अपॉइंटमेंट बुक करें") == "book_appointment"

def test_book_kannada_mixed():
    assert intent("Kal doctor appointment beku") == "book_appointment"

def test_book_telugu_mixed():
    assert intent("Repu evening appointment kavali") == "book_appointment"


# ── cancel_appointment ────────────────────────────────────────────────────────

def test_cancel_basic():
    assert intent("I want to cancel my appointment") == "cancel_appointment"

def test_cancel_call_off():
    assert intent("Please call off my appointment on Monday") == "cancel_appointment"

def test_cancel_wont_be_coming():
    assert intent("I won't be coming to the appointment") == "cancel_appointment"

def test_cancel_hindi():
    assert intent("मेरी अपॉइंटमेंट रद्द करें") == "cancel_appointment"

def test_cancel_hindi_2():
    assert intent("मुझे कैंसिल करना है") == "cancel_appointment"


# ── reschedule_appointment ────────────────────────────────────────────────────

def test_reschedule_basic():
    assert intent("I need to reschedule my appointment") == "reschedule_appointment"

def test_reschedule_change_date():
    assert intent("Can you change the date of my appointment?") == "reschedule_appointment"

def test_reschedule_another_day():
    assert intent("Can we move it to another day?") == "reschedule_appointment"

def test_reschedule_push():
    assert intent("Could you push the appointment to tomorrow? I won't be able to make it today.") == "reschedule_appointment"

def test_reschedule_cant_make_it():
    assert intent("I can't make it, can we shift it to Friday?") == "reschedule_appointment"

def test_reschedule_postpone():
    assert intent("Can we postpone it to next Monday?") == "reschedule_appointment"

def test_reschedule_hindi():
    assert intent("मेरी अपॉइंटमेंट की तारीख बदलनी है") == "reschedule_appointment"


# ── check_availability ────────────────────────────────────────────────────────

def test_availability_slot_tomorrow():
    assert intent("Is there any slot open tomorrow?") == "check_availability"

def test_availability_any_appointments():
    assert intent("Any appointments available?") == "check_availability"

def test_availability_can_i_get_slot():
    assert intent("Can I get a slot tomorrow?") == "check_availability"

def test_availability_doctor_free():
    assert intent("Is Dr Sharma free on Friday?") == "check_availability"

def test_availability_next_appointment():
    assert intent("When is the next appointment slot?") == "check_availability"

def test_availability_kannada_mixed():
    assert intent("Nale morning slot ideya?") == "check_availability"


# ── general_inquiry ───────────────────────────────────────────────────────────

def test_inquiry_hours():
    assert intent("What are the clinic hours?") == "general_inquiry"

def test_inquiry_fee():
    assert intent("What is the consultation fee?") == "general_inquiry"

def test_inquiry_hindi():
    assert intent("डॉक्टर की फीस क्या है?") == "general_inquiry"

def test_inquiry_address():
    assert intent("Where is the clinic located?") == "general_inquiry"


# ── Date: context-aware ───────────────────────────────────────────────────────

def test_date_tomorrow():
    result = entity("Book an appointment for tomorrow", "date")
    assert result == (date.today() + timedelta(days=1)).isoformat()

def test_date_context_picks_action_date():
    # "today" is the reason for cancelling; "tomorrow" is the target
    result = entity(
        "Move my appointment to tomorrow because I can't come today.", "date"
    )
    assert result == (date.today() + timedelta(days=1)).isoformat()

def test_date_push_to_tomorrow():
    result = entity(
        "Could you push the appointment to tomorrow? I won't be able to make it today.",
        "date",
    )
    assert result == (date.today() + timedelta(days=1)).isoformat()

def test_date_next_monday():
    result = entity("Schedule for next Monday", "date")
    today  = date.today()
    delta  = (0 - today.weekday() + 7) % 7 or 7
    assert result == (today + timedelta(days=delta)).isoformat()

def test_date_explicit():
    assert entity("Book on 15th April 2026", "date") == "2026-04-15"

def test_date_slash_format():
    assert entity("My appointment is on 10/06/2026", "date") == "2026-06-10"

def test_date_hindi_kal():
    result = entity("कल डॉक्टर से मिलना है", "date")
    assert result == (date.today() + timedelta(days=1)).isoformat()

def test_date_kannada_naale():
    result = entity("Naale doctor appointment beku", "date")
    assert result == (date.today() + timedelta(days=1)).isoformat()


# ── Time ──────────────────────────────────────────────────────────────────────

def test_time_morning():
    assert entity("Book for morning", "time") == "09:00"

def test_time_3pm():
    assert entity("Appointment at 3 PM", "time") == "15:00"

def test_time_1030am():
    assert entity("Schedule at 10:30 AM", "time") == "10:30"

def test_time_hindi_dopahar():
    assert entity("दोपहर में अपॉइंटमेंट चाहिए", "time") == "14:00"

def test_time_24hr():
    assert entity("Please book at 14:00", "time") == "14:00"


# ── Doctor ────────────────────────────────────────────────────────────────────

def test_doctor_named():
    assert entity("I want to see Dr. Sharma", "doctor") == "Dr. Sharma"

def test_doctor_no_dot():
    assert entity("Can I see Dr Rao tomorrow?", "doctor") == "Dr. Rao"

def test_doctor_specialization():
    assert entity("I need a cardiologist", "doctor") == "cardiologist"


# ── Patient name ──────────────────────────────────────────────────────────────

def test_patient_name_english():
    assert entity("My name is Rahul Verma", "patient_name") == "Rahul Verma"

def test_patient_name_hindi():
    assert entity("मेरा नाम राहुल है", "patient_name") is not None

def test_patient_name_not_extracted_from_symptom():
    # "not feeling well" must NOT produce a patient name
    assert entity("I am not feeling well.", "patient_name") is None


# ── Missing entities & follow-up ──────────────────────────────────────────────

def test_missing_patient_name():
    result = analyse("Book an appointment with Dr. Sharma tomorrow at 3 PM")
    assert "patient_name" in result["missing_entities"]

def test_no_missing_for_inquiry():
    result = analyse("What are the clinic timings?")
    assert result["missing_entities"] == []

def test_follow_up_missing_doctor():
    result = analyse("I want to book an appointment for tomorrow at 3 PM")
    assert result["follow_up_question"] == "Which doctor would you like to consult?"

def test_follow_up_missing_date():
    result = analyse("I want to book an appointment with Dr. Sharma at 3 PM")
    assert result["follow_up_question"] == "What date would you prefer?"

def test_follow_up_missing_time():
    result = analyse("Book an appointment with Dr. Sharma tomorrow. My name is Rahul Verma")
    assert result["follow_up_question"] == "What time works best for you?"

def test_follow_up_none_for_inquiry():
    result = analyse("What are the clinic timings?")
    assert result["follow_up_question"] is None


# ── Confidence ────────────────────────────────────────────────────────────────

def test_confidence_range():
    result = analyse("I want to book an appointment")
    assert 0.0 <= result["confidence"] <= 1.0

def test_confidence_higher_with_entities():
    few     = analyse("I want to book an appointment")
    many    = analyse("Book an appointment with Dr. Sharma tomorrow at 3 PM. My name is Rahul.")
    assert many["confidence"] >= few["confidence"]
