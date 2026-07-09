import math
from faster_whisper import WhisperModel

import config
from input.recorder import record_audio
from utils.logger import get_logger

logger = get_logger(__name__)

logger.info(
    "Loading Whisper model: %s (device: %s, compute: %s)", 
    config.WHISPER_MODEL, config.WHISPER_DEVICE, config.WHISPER_COMPUTE_TYPE
)

# Initialize the model once globally so it doesn't reload on every transcription
_model = WhisperModel(
    config.WHISPER_MODEL,
    device=config.WHISPER_DEVICE,
    compute_type=config.WHISPER_COMPUTE_TYPE
)

def transcribe(language: str = None) -> dict:
    """
    Capture audio from the microphone and transcribe it using faster-whisper.
    If language is None, faster-whisper will automatically detect the language.
    """
    logger.info("Transcription started")

    try:
        # Record audio using custom recorder with silence detection
        record_audio(
            filename=config.TEMP_AUDIO_FILE,
            max_duration=config.AUDIO_DURATION,
            silence_threshold=config.SILENCE_THRESHOLD,
            silence_duration=config.SILENCE_DURATION,
        )

        logger.info("Audio captured | transcribing...")
        
        # Transcribe using faster-whisper
        segments, info = _model.transcribe(
            config.TEMP_AUDIO_FILE, 
            beam_size=5,
            language=language,
            task="translate"
        )

        detected_lang = info.language
        lang_prob = info.language_probability

        text = ""
        logprobs = []

        # We must iterate over segments to actually perform the transcription
        for segment in segments:
            text += segment.text + " "
            logprobs.append(segment.avg_logprob)

        text = text.strip()

        # Calculate a rough confidence score (0 to 1) based on average logprob
        if logprobs:
            avg_logprob = sum(logprobs) / len(logprobs)
            confidence = math.exp(avg_logprob)
        else:
            confidence = 0.0

        confidence = round(confidence, 4)

        logger.info(
            "Transcription completed | lang=%s (prob=%.2f) | confidence=%.2f | text_length=%d",
            detected_lang, lang_prob, confidence, len(text),
        )

        return {"text": text, "language": detected_lang, "confidence": confidence}

    except Exception:
        logger.exception("Unexpected error during transcription")
        return {"text": "", "language": "unknown", "confidence": 0.0}
