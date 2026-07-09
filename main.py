import config
from processing.stt import transcribe
from processing.nlp import analyse
from utils.logger import get_logger

logger = get_logger(__name__)


def _print_divider():
    print("-" * 50)


def _print_stt_result(result: dict):
    print(f"\n  Language   : {result['language']}")
    print(f"  Confidence : {result['confidence']:.2%}")
    print(f"  Transcript : {result['text']}")


def _print_nlp_result(nlp: dict):
    print(f"\n  Intent     : {nlp['intent']}")
    print(f"  Confidence : {nlp['confidence']:.2%}")

    entities = nlp["entities"]
    print("  Entities   :")
    for key, value in entities.items():
        print(f"    {key:<15}: {value}")

    if nlp["missing_entities"]:
        print(f"\n  Missing    : {', '.join(nlp['missing_entities'])}")

    if nlp["follow_up_question"]:
        print(f"\n  Follow-up  : {nlp['follow_up_question']}")


def main():
    print("=== VoxMed AI ===")
    print("Select Language:")
    print("[0] Auto-Detect")
    for key, lang_info in config.SUPPORTED_LANGUAGES.items():
        print(f"[{key}] {lang_info['name']}")

    lang_choice = input("Choice [0]: ").strip()

    if lang_choice in config.SUPPORTED_LANGUAGES:
        lang_code = config.SUPPORTED_LANGUAGES[lang_choice]["code"].split("-")[0]
        print(f"\nSelected: {config.SUPPORTED_LANGUAGES[lang_choice]['name']}")
    else:
        lang_code = None
        print("\nSelected: Auto-Detect")

    while True:
        print("\nPress Enter to start recording...")
        input()

        # ── Stage 1: Record + Transcribe ─────────────────────────────────────
        logger.info("Pipeline started")
        stt_result = transcribe(language=lang_code)

        if not stt_result["text"]:
            print("\n  Could not transcribe audio. Please try again.")
            continue

        if stt_result["confidence"] < 0.4:
            print("\n  Low confidence transcription. Please speak clearly and try again.")
            continue

        _print_divider()
        print("[Transcription]")
        _print_stt_result(stt_result)

        # ── Stage 2: NLP ──────────────────────────────────────────────────────
        nlp_result = analyse(stt_result["text"])
        logger.info(
            "Pipeline completed | intent=%s | missing=%s",
            nlp_result["intent"],
            nlp_result["missing_entities"],
        )

        _print_divider()
        print("[NLP]")
        _print_nlp_result(nlp_result)
        _print_divider()

        choice = input("\nRecord again? (y/n): ").strip().lower()
        if choice != "y":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()
