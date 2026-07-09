"""
processing/nlp.py
-----------------
Intent detection and entity extraction for VoxMed AI.

Architecture
------------
BaseNLPEngine      – abstract interface (swap in Rasa/OpenAI later)
RuleBasedEngine    – semantic pattern + regex engine, fully offline
analyse(text)      – module-level convenience function

Design principles
-----------------
- Patterns are phrase-level, not single keywords, so paraphrases match
- Each intent has an explicit priority so specific intents beat generic ones
- Date extraction finds ALL date mentions then picks the one tied to the action
- Patient name extraction only fires on explicit introduction phrases
- Confidence is computed from match strength, entity coverage, and conflicts
- follow_up_question returns ONE natural question for the first missing entity
- Supports English, Hindi, Kannada, Telugu and code-mixed sentences
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Any

from utils.logger import get_logger

logger = get_logger(__name__)

# ── Intents ───────────────────────────────────────────────────────────────────

INTENTS = (
    "book_appointment",
    "cancel_appointment",
    "reschedule_appointment",
    "check_availability",
    "general_inquiry",
)

# Higher number = higher priority when scores tie
_INTENT_PRIORITY: dict[str, int] = {
    "reschedule_appointment": 5,
    "cancel_appointment":     4,
    "check_availability":     3,
    "book_appointment":       2,
    "general_inquiry":        1,
}

REQUIRED_ENTITIES: dict[str, list[str]] = {
    "book_appointment":       ["doctor", "date", "time", "patient_name"],
    "cancel_appointment":     ["patient_name", "date"],
    "reschedule_appointment": ["date", "time", "patient_name"],
    "check_availability":     ["date"],
    "general_inquiry":        [],
}

# Single follow-up question per missing entity (priority order matters)
_FOLLOW_UP: dict[str, str] = {
    "doctor":       "Which doctor would you like to consult?",
    "date":         "What date would you prefer?",
    "time":         "What time works best for you?",
    "patient_name": "May I know the patient's name?",
}

# ── Symptom guard — words that must NOT be mistaken for patient names ─────────

_SYMPTOM_WORDS = {
    "feeling", "well", "sick", "fever", "pain", "cold", "cough", "tired",
    "weak", "dizzy", "nausea", "vomiting", "headache", "unwell", "ill",
    "बुखार", "दर्द", "खांसी", "थकान", "चक्कर", "उल्टी", "बीमार",
}

# ── Abstract interface ────────────────────────────────────────────────────────

class BaseNLPEngine(ABC):
    @abstractmethod
    def analyse(self, text: str) -> dict[str, Any]:
        """
        Returns:
        {
            "intent":            str,
            "confidence":        float,
            "entities":          dict,
            "missing_entities":  list[str],
            "follow_up_question": str | None,
        }
        """

# ── Rule-based engine ─────────────────────────────────────────────────────────

class RuleBasedEngine(BaseNLPEngine):

    # ── Semantic pattern groups ───────────────────────────────────────────────
    # Each entry is a regex pattern (case-insensitive, applied to lowercased text).
    # Phrase-level patterns beat single-word keyword matching for paraphrases.

    _PATTERNS: dict[str, list[str]] = {

        "book_appointment": [
            # English — explicit booking
            r"\bbook\b.*\bappointment\b",
            r"\bschedule\b.*\bappointment\b",
            r"\bmake\b.*\bappointment\b",
            r"\bfix\b.*\bappointment\b",
            r"\bset up\b.*\bappointment\b",
            r"\barrange\b.*\bappointment\b",
            r"\bregister\b.*\bappointment\b",
            r"\bi('d| would) like an appointment\b",
            r"\bi need (to see|to consult|a doctor|an appointment)\b",
            r"\bi want to (see|meet|consult|visit) (dr\.?|doctor)\b",
            r"\bcan i see (dr\.?|doctor)\b",
            r"\bappointment (chahiye|lena|book)\b",   # Hindi
            r"\b(doctor|डॉक्टर) se milna\b",
            r"\bappointment\b.*\b(beku|beda)\b",      # Kannada
            r"\bappointment\b.*\bkavali\b",            # Telugu
            r"\bnale\b.*\b(doctor|appointment)\b",     # Kannada: naale = tomorrow
            r"\brepu\b.*\b(doctor|appointment)\b",     # Telugu/Kannada: repu = tomorrow
            r"\bkal\b.*\b(doctor|appointment)\b",      # Hindi: kal = tomorrow
            r"\bappointment\b.*\bnaale\b",
            r"\bappointment\b.*\brepu\b",
            r"\bappointment\b.*\bkal\b",
            # Hindi script
            r"अपॉइंटमेंट.*(लेना|बुक|चाहिए)",
            r"डॉक्टर से मिलना",
            r"समय लेना",
        ],

        "cancel_appointment": [
            # English
            r"\bcancel\b.*\b(appointment|booking|slot)\b",
            r"\b(appointment|booking)\b.*\bcancel\b",
            r"\bcall off\b.*\bappointment\b",
            r"\bremove\b.*\bappointment\b",
            r"\bdrop\b.*\bappointment\b",
            r"\bi (won't|will not|wont) be (coming|there|able to make it)\b",
            r"\bnot coming\b",
            r"\bdon't want the appointment\b",
            # Hindi script
            r"अपॉइंटमेंट.*(रद्द|कैंसिल)",
            r"(रद्द|कैंसिल) करना",
            r"नहीं आना",
            # Hindi romanised
            r"\b(appointment|booking)\b.*\b(cancel|radd)\b",
            r"\bradd\b.*\bkarna\b",
        ],

        "reschedule_appointment": [
            # English
            r"\breschedule\b",
            r"\b(change|shift|move|push|postpone|defer)\b.*(appointment|slot|booking|it|date|time)\b",
            r"\b(appointment|slot|booking|it)\b.*(change|shift|move|push|postpone)\b",
            r"\banother (day|time|slot|date)\b",
            r"\bdifferent (day|time|slot|date)\b",
            r"\bcan('t| not|not) make it\b",
            r"\bwon'?t be able to make it\b",
            r"\bunable to (come|make it|attend)\b",
            r"\bput it off\b",
            r"\bdelay (my|the) appointment\b",
            # Hindi script
            r"(तारीख|समय|अपॉइंटमेंट).*(बदल)",
            r"बदलना है",
            r"दूसरे दिन",
            # Hindi romanised
            r"\b(date|time|appointment)\b.*\bbadalna\b",
            r"\bbadalna\b",
            # Kannada
            r"\b(appointment|date|time)\b.*\bbadlisu\b",
            # Telugu
            r"\b(appointment|date|time)\b.*\bmarchu\b",
        ],

        "check_availability": [
            # English
            r"\b(any|is there a?|check)\b.*(slot|opening|appointment|availability)\b",
            r"\b(slot|opening|appointment)\b.*(available|open|free|there)\b",
            r"\bis (dr\.?|doctor)\b.*\bfree\b",
            r"\bwhen is (the next|a) (slot|appointment|opening)\b",
            r"\bdo you have (any|an) (opening|slot|appointment)\b",
            r"\bcan i get a slot\b",
            r"\bany (slots?|appointments?)\b",
            # Kannada
            r"\bslot\b.*\bideya\b",
            r"\bideya\b.*\bslot\b",
            r"\bnale\b.*\bslot\b",
            r"\bnaale\b.*\bslot\b",
            # Telugu
            r"\bslot\b.*\bundha\b",
            r"\brepu\b.*\bslot\b",
            # Hindi
            r"\bkoi\b.*\bslot\b",
            r"कोई.*(स्लॉट|अपॉइंटमेंट).*(है|उपलब्ध)",
        ],

        "general_inquiry": [
            r"\b(what|when|where|how|which|who)\b.*(clinic|hospital|doctor|fee|cost|hour|timing|address|location)\b",
            r"\btell me (about|the)\b",
            r"\b(fee|cost|price|charge)\b.*(consult|appointment|visit)\b",
            r"\b(timing|hours?|open|close)\b.*(clinic|hospital|doctor)\b",
            r"\bwhere (is|are)\b.*(clinic|hospital|doctor)\b",
            # Hindi script
            r"(फीस|पता|समय|जानकारी).*(क्या|बताइए|है)",
            r"क्या.*(फीस|पता|समय)",
        ],
    }

    # ── Date vocabulary ───────────────────────────────────────────────────────

    _WEEKDAYS: dict[str, int] = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
        "सोमवार": 0, "मंगलवार": 1, "बुधवार": 2, "गुरुवार": 3,
        "शुक्रवार": 4, "शनिवार": 5, "रविवार\u200c": 6,
    }

    _MONTHS: dict[str, int] = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
        "jan": 1, "feb": 2, "mar": 3, "apr": 4,
        "jun": 6, "jul": 7, "aug": 8, "sep": 9,
        "oct": 10, "nov": 11, "dec": 12,
    }

    # Action prepositions — a date following these belongs to the requested action
    _ACTION_PREPS = re.compile(
        r"\b(to|for|on|at|by|naale|repu|kal|nale)\b\s*(.{0,40})",
        re.IGNORECASE,
    )

    # ── Time vocabulary ───────────────────────────────────────────────────────

    _TIME_KEYWORDS: dict[str, str] = {
        "morning": "09:00", "afternoon": "14:00",
        "evening": "17:00", "night":     "20:00",
        "noon":    "12:00", "midnight":  "00:00",
        # Hindi
        "सुबह": "09:00", "दोपहर": "14:00",
        "शाम":  "17:00", "रात":   "20:00",
        # Kannada / Telugu
        "beligge": "09:00", "madhyahna": "14:00",
        "sanje":   "17:00", "raatri":    "20:00",
    }

    # ── Specializations ───────────────────────────────────────────────────────

    _SPECIALIZATIONS: list[str] = [
        "cardiologist", "dermatologist", "neurologist", "orthopedic",
        "pediatrician", "gynecologist", "psychiatrist", "dentist",
        "ophthalmologist", "general physician", "surgeon", "urologist",
        "endocrinologist", "oncologist", "radiologist",
        "हृदय रोग विशेषज्ञ", "त्वचा विशेषज्ञ", "न्यूरोलॉजिस्ट",
        "बाल रोग विशेषज्ञ", "दंत चिकित्सक",
    ]

    # ── Public API ────────────────────────────────────────────────────────────

    def analyse(self, text: str) -> dict[str, Any]:
        logger.info("NLP analysis started | text_length=%d", len(text))

        lower = text.strip().lower()

        intent, confidence = self._detect_intent(lower)
        entities           = self._extract_entities(text, lower)
        required           = REQUIRED_ENTITIES.get(intent, [])
        missing            = [k for k in required if not entities.get(k)]
        follow_up          = self._follow_up_question(missing)

        # Refine confidence using entity coverage
        confidence = self._adjust_confidence(confidence, intent, entities, missing)

        result: dict[str, Any] = {
            "intent":            intent,
            "confidence":        confidence,
            "entities":          entities,
            "missing_entities":  missing,
            "follow_up_question": follow_up,
        }

        logger.info(
            "NLP analysis completed | intent=%s | confidence=%.2f | missing=%s",
            intent, confidence, missing,
        )
        return result

    # ── Intent detection ──────────────────────────────────────────────────────

    def _detect_intent(self, lower: str) -> tuple[str, float]:
        """
        Score each intent by counting how many of its semantic patterns match.
        Ties are broken by _INTENT_PRIORITY so specific intents beat generic ones.
        """
        scores: dict[str, int] = {}

        for intent, patterns in self._PATTERNS.items():
            scores[intent] = sum(
                1 for p in patterns if re.search(p, lower, re.IGNORECASE)
            )

        best_score = max(scores.values())

        if best_score == 0:
            return "general_inquiry", 0.4

        # Among intents with the best score, pick the highest-priority one
        candidates = [i for i, s in scores.items() if s == best_score]
        best_intent = max(candidates, key=lambda i: _INTENT_PRIORITY[i])

        # Confidence: matched patterns / total patterns for that intent
        total_patterns = len(self._PATTERNS[best_intent])
        raw_confidence = best_score / total_patterns

        # Penalise when a competing intent also scored
        competing = [i for i, s in scores.items() if s > 0 and i != best_intent]
        penalty = 0.05 * len(competing)

        confidence = round(max(0.1, min(1.0, raw_confidence - penalty)), 4)
        return best_intent, confidence

    # ── Confidence adjustment ─────────────────────────────────────────────────

    def _adjust_confidence(
        self,
        base: float,
        intent: str,
        entities: dict,
        missing: list[str],
    ) -> float:
        """Boost confidence when entities are present; penalise when many are missing."""
        filled  = sum(1 for k in REQUIRED_ENTITIES.get(intent, []) if entities.get(k))
        total   = len(REQUIRED_ENTITIES.get(intent, [])) or 1
        boost   = 0.05 * filled
        penalty = 0.04 * len(missing)
        return round(max(0.1, min(1.0, base + boost - penalty)), 4)

    # ── Entity extraction ─────────────────────────────────────────────────────

    def _extract_entities(self, original: str, lower: str) -> dict[str, Any]:
        return {
            "patient_name": self._extract_patient_name(original),
            "doctor":       self._extract_doctor(original, lower),
            "date":         self._extract_date(lower),
            "time":         self._extract_time(lower),
        }

    # ── Patient name ──────────────────────────────────────────────────────────

    def _extract_patient_name(self, original: str) -> str | None:
        """
        Only extract a name when the sentence explicitly introduces a person.
        Guards against symptom words being captured as names.
        """
        patterns = [
            # English — must follow an introduction phrase
            r"(?:my name is|i am|i'm|name is|patient(?:'s)? name is|patient is)\s+"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            # Hindi script
            r"(?:मेरा नाम|नाम है)\s+([\u0900-\u097F]+(?:\s+[\u0900-\u097F]+)?)",
        ]
        for pattern in patterns:
            m = re.search(pattern, original, re.IGNORECASE)
            if m:
                name = m.group(1).strip()
                # Reject if any word in the name is a symptom word
                if not any(w.lower() in _SYMPTOM_WORDS for w in name.split()):
                    return name
        return None

    # ── Doctor ────────────────────────────────────────────────────────────────

    def _extract_doctor(self, original: str, lower: str) -> str | None:
        # Named: "Dr. Sharma", "Dr Rao", "doctor Kapoor"
        m = re.search(r"\b(?:dr\.?|doctor)\s+([A-Za-z]+)", original, re.IGNORECASE)
        if m:
            return f"Dr. {m.group(1).capitalize()}"

        # Hindi script named doctor
        m = re.search(r"डॉ\.?\s+([\u0900-\u097F]+)", original)
        if m:
            return f"डॉ. {m.group(1)}"

        # Specialization fallback
        for spec in self._SPECIALIZATIONS:
            if spec in lower:
                return spec

        return None

    # ── Date ──────────────────────────────────────────────────────────────────

    def _extract_date(self, text: str) -> str | None:
        """
        Find all date mentions in the text, then return the one that is
        closest to an action preposition (to/for/on/naale/repu/kal).
        This prevents "today" in "I can't come today, move it to tomorrow"
        from being returned instead of "tomorrow".
        """
        candidates: list[tuple[int, str]] = []  # (position, iso_date)

        today = date.today()

        # ── Collect all date mentions with their position ─────────────────────

        for m in re.finditer(r"\btoday\b|आज", text):
            candidates.append((m.start(), today.isoformat()))

        for m in re.finditer(r"\btomorrow\b|कल|kal\b|naale\b|nale\b|repu\b", text):
            candidates.append((m.start(), (today + timedelta(days=1)).isoformat()))

        for m in re.finditer(r"\bday after tomorrow\b|परसों", text):
            candidates.append((m.start(), (today + timedelta(days=2)).isoformat()))

        # "next <weekday>"
        for m in re.finditer(r"\bnext\s+(\w+)", text):
            day_name = m.group(1).lower()
            if day_name in self._WEEKDAYS:
                delta = (self._WEEKDAYS[day_name] - today.weekday() + 7) % 7 or 7
                candidates.append((m.start(), (today + timedelta(days=delta)).isoformat()))

        # Hindi / Kannada / Telugu weekday names
        for day_name, day_num in self._WEEKDAYS.items():
            if not day_name.isascii():
                for m in re.finditer(re.escape(day_name), text):
                    delta = (day_num - today.weekday() + 7) % 7 or 7
                    candidates.append((m.start(), (today + timedelta(days=delta)).isoformat()))

        # "15th April 2026", "April 15"
        ordinal = r"(\d{1,2})(?:st|nd|rd|th)?"
        month_re = "|".join(self._MONTHS)

        for m in re.finditer(
            ordinal + r"\s+(?:of\s+)?(" + month_re + r")(?:\s+(\d{4}))?", text
        ):
            day   = int(m.group(1))
            month = self._MONTHS[m.group(2)]
            year  = int(m.group(3)) if m.group(3) else today.year
            d = _safe_date(year, month, day)
            if d:
                candidates.append((m.start(), d))

        for m in re.finditer(
            r"(" + month_re + r")\s+" + ordinal + r"(?:\s+(\d{4}))?", text
        ):
            month = self._MONTHS[m.group(1)]
            day   = int(m.group(2))
            year  = int(m.group(3)) if m.group(3) else today.year
            d = _safe_date(year, month, day)
            if d:
                candidates.append((m.start(), d))

        # DD/MM/YYYY
        for m in re.finditer(r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})", text):
            d = _safe_date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            if d:
                candidates.append((m.start(), d))

        # YYYY-MM-DD
        for m in re.finditer(r"(\d{4})-(\d{2})-(\d{2})", text):
            d = _safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if d:
                candidates.append((m.start(), d))

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0][1]

        # ── Pick the date closest (after) an action preposition ───────────────
        action_positions = [m.start() for m in self._ACTION_PREPS.finditer(text)]

        if action_positions:
            # For each candidate, find the nearest action prep that precedes it
            def _score(pos_date: tuple[int, str]) -> int:
                pos = pos_date[0]
                preceding = [ap for ap in action_positions if ap <= pos]
                if not preceding:
                    return 9999  # no preceding action prep → deprioritise
                return pos - max(preceding)

            candidates.sort(key=_score)
            return candidates[0][1]

        # Fallback: return the last date mentioned (most likely the target)
        return candidates[-1][1]

    # ── Time ──────────────────────────────────────────────────────────────────

    def _extract_time(self, text: str) -> str | None:
        for keyword, value in self._TIME_KEYWORDS.items():
            if keyword in text:
                return value

        # "3 PM", "3:30 PM", "3pm"
        m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", text, re.IGNORECASE)
        if m:
            hour     = int(m.group(1))
            minute   = int(m.group(2)) if m.group(2) else 0
            meridiem = m.group(3).lower()
            if meridiem == "pm" and hour != 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0
            return f"{hour:02d}:{minute:02d}"

        # 24-hour "14:30"
        m = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
        if m:
            return f"{int(m.group(1)):02d}:{int(m.group(2)):02d}"

        return None

    # ── Follow-up question ────────────────────────────────────────────────────

    def _follow_up_question(self, missing: list[str]) -> str | None:
        """Return ONE question for the highest-priority missing entity."""
        for entity in _FOLLOW_UP:          # dict is insertion-ordered by priority
            if entity in missing:
                return _FOLLOW_UP[entity]
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_date(year: int, month: int, day: int) -> str | None:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


# ── Module-level singleton + convenience function ─────────────────────────────

_engine = RuleBasedEngine()


def analyse(text: str) -> dict[str, Any]:
    """Module-level convenience wrapper. Public API — do not rename."""
    return _engine.analyse(text)
