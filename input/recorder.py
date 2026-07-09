import pyaudio
import wave
import config
from utils.logger import get_logger

logger = get_logger(__name__)

def record_audio(filename=config.TEMP_AUDIO_FILE, duration=config.AUDIO_DURATION):
    CHUNK = config.AUDIO_CHUNK
    FORMAT = pyaudio.paInt16
    CHANNELS = config.AUDIO_CHANNELS
    RATE = config.AUDIO_RATE

    logger.info(
        "Audio recording started | file=%s | duration=%ss | rate=%s | channels=%s",
        filename, duration, RATE, CHANNELS
    )

    try:
        p = pyaudio.PyAudio()

        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        frames = []

        for _ in range(int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK)
            frames.append(data)

        logger.info("Audio recording completed | frames_collected=%s", len(frames))

        stream.stop_stream()
        stream.close()

        # Save file
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        logger.info("Audio file saved successfully | path=%s", filename)

        p.terminate()

    except Exception as e:
        logger.exception("Audio recording failed | file=%s", filename)