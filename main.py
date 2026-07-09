import config
from processing.stt import transcribe
from processing.translator import translate_to_english

def main():
    print("=== VoxMed AI ===")
    print("Select Language:")
    print("[0] Auto-Detect (Mixed languages)")
    for key, lang_info in config.SUPPORTED_LANGUAGES.items():
        print(f"[{key}] {lang_info['name']}")
    
    lang_choice = input(f"Choice [0]: ").strip()
    
    if lang_choice in config.SUPPORTED_LANGUAGES:
        raw_code = config.SUPPORTED_LANGUAGES[lang_choice]["code"]
        lang_code = raw_code.split('-')[0] # faster-whisper expects 'hi', not 'hi-IN'
        print(f"\nSelected language: {config.SUPPORTED_LANGUAGES[lang_choice]['name']}")
    else:
        lang_code = None
        print("\nSelected language: Auto-Detect")

    while True:
        print("\nPress Enter to start recording...")
        input()

        result = transcribe(language=lang_code)

        if not result["text"] or result["confidence"] < 0.4:
            print("\nSorry, I didn't catch that clearly. Let's try again.")
            continue

        print(f"\nLanguage   : {result['language']}")
        print(f"Confidence : {result['confidence']:.2%}")
        print(f"Transcript : {result['text']}")

        if result['language'] != 'en':
            english_text = translate_to_english(result['text'], result['language'])
            print(f"In English : {english_text}")
            
        print() # Extra newline


        choice = input("Record again? (y/n): ").strip().lower()

        if choice != "y":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()