# VoxMed AI – Task Progress Tracker

> Last updated: 2026-04-07  
> Current Phase: **Phase 1 – Project Foundation**  

---

## ✅ PHASE 1: Project Foundation

### Done
- [x] Created folder structure: `services/`, `api/`, `admin/`, `tests/` with `__init__.py`
- [x] Created `config.py` – centralized constants (paths, audio, languages, DB, API)
- [x] Committed and pushed to GitHub (`68417fa`)

### 🔲 Remaining in Phase 1 (Pick up here next time)

**Step 3 – `utils/logger.py`** ← NEXT UP
> Create a centralized logger that writes to both terminal + file.
> Code to write:
```python
# utils/logger.py – Centralized logging for VoxMed AI
import logging
import sys
from pathlib import Path
import config


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger for the given module name.
    Usage: logger = get_logger(__name__)
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    Path(config.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(config.LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
```
> Test command:
```bash
cd /Users/kapilpal/voxmed/VoxMed-AI
python3 -c "
from utils.logger import get_logger
logger = get_logger('test')
logger.info('VoxMed AI logger initialized successfully')
logger.warning('This is a warning message')
logger.error('This is an error message')
"
```
> Expected: Timestamped log lines in terminal + written to `output/voxmed.log`

---

**Step 4 – `utils/validators.py`**
> Input validation helpers (validate date, time, phone number format).
> Will be built after logger is done.

---

**Step 5 – Update `requirements.txt`**
> Replace current content with:
```
SpeechRecognition
pyaudio
pyttsx3
fastapi
uvicorn
python-dotenv
```

---

**Step 6 – Update `.gitignore`**
> Add these lines:
```
.env
*.db
output/*.wav
output/*.log
venv/
```

---

**Step 7 – Create stub files for processing modules**
> These will be empty for now but establish the module structure:
- `processing/stt.py`
- `processing/tts.py`
- `processing/nlp.py`
- `processing/dialogue.py`
- `services/appointments.py`
- `api/server.py`

---

**Step 8 – Wire up `main.py`** ← Phase 1 final milestone
> Connect recorder → transcriber → print output in a simple CLI loop.
> This will be the first time the full audio pipeline runs end-to-end!

---

## 🔲 PHASE 2: Microphone Integration (Not Started)
- Refactor `input/recorder.py` with silence detection
- Create `processing/stt.py` (replace transcriber.py)
- Support live mic + language parameter

## 🔲 PHASE 3: Multilingual STT (Not Started)
- Auto language detection
- Handle mixed English/Hindi input
- Retry on unclear audio

## 🔲 PHASE 4: NLP – Intent + Entities (Not Started)
- `processing/nlp.py`
- 4 intents: book, cancel, reschedule, inquiry
- 4 entities: name, doctor, date, time

## 🔲 PHASE 5: Dialogue Manager (Not Started)
- `processing/dialogue.py`
- State machine: GREETING → INTENT_CAPTURE → SLOT_FILLING → CONFIRMATION → ACTION → FAREWELL

## 🔲 PHASE 6: Appointments + Database (Not Started)
- `database.py` with SQLite schema
- `services/appointments.py` – booking engine

## 🔲 PHASE 7: Text-to-Speech (Not Started)
- `processing/tts.py` using pyttsx3

## 🔲 PHASE 8: Admin Dashboard (Not Started)
- `api/server.py` – FastAPI REST endpoints
- `admin/` – HTML/CSS/JS web UI

## 🔲 PHASE 9: Testing & Edge Cases (Not Started)
- Full test suite in `tests/`
- Edge case handling

## 🔲 PHASE 10: Deployment & API Migration (Not Started)
- Twilio integration
- Cloud STT/TTS APIs
- Production deployment
