import config
from input.recorder import record_audio
from processing.transcriber import transcribe_audio
from processing.translator import translate_to_english

def main():
    print("=== VoxMed AI ===")
    print("Select Language:")
    for key, lang_info in config.SUPPORTED_LANGUAGES.items():
        print(f"[{key}] {lang_info['name']}")
    
    lang_choice = input(f"Choice [{config.DEFAULT_LANGUAGE}]: ").strip()
    if lang_choice not in config.SUPPORTED_LANGUAGES:
        lang_choice = config.DEFAULT_LANGUAGE
        
    lang_code = config.SUPPORTED_LANGUAGES[lang_choice]["code"]
    lang_name = config.SUPPORTED_LANGUAGES[lang_choice]["name"]
    print(f"\nSelected language: {lang_name}")

    while True:
        print("\nPress Enter to start recording...")
        input()

        record_audio()

        text = transcribe_audio(language_code=lang_code)

        if text:
            print(f"\nYou said ({lang_name}): {text}")
            
            # Translate if not English
            if lang_code != "en-US":
                english_text = translate_to_english(text, source_lang_code=lang_code)
                print(f"In English: {english_text}")
        else:
            print("\nCould not hear anything.")

        print() # Empty line for spacing
        choice = input("Record again? (y/n): ").strip().lower()

        if choice != "y":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()
