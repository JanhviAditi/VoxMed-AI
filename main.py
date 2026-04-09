from input.recorder import record_audio
from processing.transcriber import transcribe_audio
from utils.logger import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    filename = "test_output.wav"

    logger.info("Pipeline started")

    record_audio(filename=filename, duration=5)

    text = transcribe_audio(filename)

    logger.info("Final transcription output | text=%s", text)

    print("\nFinal Output:")
    print(text)