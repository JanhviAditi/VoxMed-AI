"""
processing/dialogue.py
----------------------
State machine for dialogue management.
"""

from typing import Any
from utils.logger import get_logger

logger = get_logger(__name__)

class DialogueState:
    GREETING = "GREETING"
    INTENT_CAPTURE = "INTENT_CAPTURE"
    SLOT_FILLING = "SLOT_FILLING"
    CONFIRMATION = "CONFIRMATION"
    ACTION = "ACTION"
    FAREWELL = "FAREWELL"

class DialogueManager:
    def __init__(self):
        self.state = DialogueState.GREETING
        self.intent = None
        self.entities = {}
        self.missing_entities = []
        logger.info("DialogueManager initialized")

    def get_greeting(self) -> str:
        self.state = DialogueState.INTENT_CAPTURE
        return "Welcome to VoxMed AI. How can I help you today?"

    def process(self, user_text: str, nlp_result: dict[str, Any]) -> str:
        logger.info("DM processing | state=%s | intent=%s", self.state, nlp_result.get("intent"))

        if self.state == DialogueState.GREETING:
            return self.get_greeting()

        if self.state == DialogueState.INTENT_CAPTURE:
            return self._handle_intent_capture(nlp_result)

        if self.state == DialogueState.SLOT_FILLING:
            return self._handle_slot_filling(nlp_result)

        if self.state == DialogueState.CONFIRMATION:
            return self._handle_confirmation(nlp_result)

        if self.state in [DialogueState.ACTION, DialogueState.FAREWELL]:
            return "The conversation has ended."
            
        return "I'm sorry, I encountered an error."

    def _update_entities(self, new_entities: dict):
        for k, v in new_entities.items():
            if v is not None:
                self.entities[k] = v

    def _handle_intent_capture(self, nlp_result: dict) -> str:
        self.intent = nlp_result["intent"]
        self._update_entities(nlp_result["entities"])
        self.missing_entities = nlp_result["missing_entities"]

        if self.intent == "general_inquiry":
            self.state = DialogueState.FAREWELL
            return "For general inquiries, our clinic is open Monday to Saturday, 9 AM to 8 PM. Is there anything else you need?"
            
        if self.missing_entities:
            self.state = DialogueState.SLOT_FILLING
            return nlp_result["follow_up_question"]
            
        self.state = DialogueState.CONFIRMATION
        return self._generate_confirmation_prompt()

    def _handle_slot_filling(self, nlp_result: dict) -> str:
        # In SLOT_FILLING, the nlp_result intent might be low confidence because
        # the user just said "tomorrow". We just care about the extracted entities.
        self._update_entities(nlp_result["entities"])
        
        # Recalculate missing entities based on current intent requirements
        from processing.nlp import REQUIRED_ENTITIES, _FOLLOW_UP
        required = REQUIRED_ENTITIES.get(self.intent, [])
        self.missing_entities = [k for k in required if not self.entities.get(k)]
        
        if self.missing_entities:
            # Ask the next missing entity
            next_missing = self.missing_entities[0]
            return _FOLLOW_UP[next_missing]
            
        self.state = DialogueState.CONFIRMATION
        return self._generate_confirmation_prompt()

    def _handle_confirmation(self, nlp_result: dict) -> str:
        intent = nlp_result["intent"]
        
        if intent == "affirm":
            self.state = DialogueState.ACTION
            return self._execute_action()
        elif intent == "deny":
            # Reset and ask what they want to do
            self.state = DialogueState.INTENT_CAPTURE
            self.intent = None
            self.entities = {}
            return "Alright, let's start over. What would you like to do?"
        else:
            return "Please answer 'yes' or 'no'. " + self._generate_confirmation_prompt()

    def _generate_confirmation_prompt(self) -> str:
        if self.intent == "book_appointment":
            doc = self.entities.get("doctor", "a doctor")
            return f"You want to book an appointment with {doc} on {self.entities.get('date')} at {self.entities.get('time')} for {self.entities.get('patient_name')}. Is that correct?"
        elif self.intent == "cancel_appointment":
            return f"You want to cancel the appointment on {self.entities.get('date')} for {self.entities.get('patient_name')}. Is that correct?"
        elif self.intent == "reschedule_appointment":
            return f"You want to reschedule the appointment for {self.entities.get('patient_name')} to {self.entities.get('date')} at {self.entities.get('time')}. Is that correct?"
        elif self.intent == "check_availability":
            return f"You want to check availability for {self.entities.get('date')}. Is that correct?"
        return "Is this correct?"

    def _execute_action(self) -> str:
        self.state = DialogueState.FAREWELL
        from services import appointments
        
        if self.intent == "book_appointment":
            success, msg = appointments.book_appointment(
                self.entities.get("patient_name"),
                self.entities.get("doctor", "General Physician"),
                self.entities.get("date"),
                self.entities.get("time")
            )
            return msg
            
        elif self.intent == "cancel_appointment":
            success, msg = appointments.cancel_appointment(
                self.entities.get("patient_name"),
                self.entities.get("date")
            )
            return msg
            
        elif self.intent == "reschedule_appointment":
            success, msg = appointments.reschedule_appointment(
                self.entities.get("patient_name"),
                self.entities.get("date"),
                self.entities.get("time")
            )
            return msg
            
        elif self.intent == "check_availability":
            success, msg = appointments.check_availability(
                self.entities.get("date")
            )
            return msg
            
        return "Action completed successfully."
