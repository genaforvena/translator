import argparse
import dl_translate as dlt
import chardet
import re
from googletrans import Translator

def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    return result['encoding']

def read_file_with_encoding(file_path, encoding):
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            return file.read()
    except UnicodeDecodeError:
        print(f"Failed to read with {encoding} encoding. Trying fallback encodings...")
        fallback_encodings = ['utf-8', 'windows-1251', 'koi8-r', 'iso-8859-5']
        for enc in fallback_encodings:
            if enc != encoding:
                try:
                    with open(file_path, 'r', encoding=enc) as file:
                        print(f"Successfully read file with {enc} encoding.")
                        return file.read()
                except UnicodeDecodeError:
                    continue
        raise ValueError("Unable to decode the file with any of the attempted encodings.")

def initialize_models():
    return dlt.TranslationModel(), Translator()

def split_into_paragraphs(text):
    return text.split('\n\n')

def split_long_paragraph(paragraph, max_length=500):
    words = paragraph.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(' '.join(current_chunk)) > max_length:
            chunks.append(' '.join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def is_repetitive(text):
    words = text.split()
    if len(words) < 10:
        return False
    repetitions = len(words) // 10
    return len(set(words[:repetitions])) < repetitions // 2

def translate_chunk(chunk, model, fallback_translator, max_retries=3):
    for _ in range(max_retries):
        translation = model.translate(chunk, source="ru", target="en")
        if not is_repetitive(translation):
            return translation

    print("Warning: Main translation failed. Using fallback translator.")
    return fallback_translator.translate(chunk, src='ru', dest='en').text

def translate_large_text(text, model, fallback_translator):
    paragraphs = split_into_paragraphs(text)
    
    translated_paragraphs = []
    for i, paragraph in enumerate(paragraphs):
        if paragraph.strip():
            chunks = split_long_paragraph(paragraph)
            translated_chunks = [translate_chunk(chunk, model, fallback_translator) for chunk in chunks]
            translated_paragraph = ' '.join(translated_chunks)
            translated_paragraphs.append(translated_paragraph)
            
            print(f"\nParagraph {i+1}/{len(paragraphs)}:")
            print(f"Original: {paragraph[:100]}..." if len(paragraph) > 100 else f"Original: {paragraph}")
            print(f"Translated: {translated_paragraph[:100]}..." if len(translated_paragraph) > 100 else f"Translated: {translated_paragraph}")
            print("-" * 80)
    
    return '\n\n'.join(translated_paragraphs)

def main():
    parser = argparse.ArgumentParser(description="Translate Russian text file to English")
    parser.add_argument("input", help="Path to the input Russian text file")
    parser.add_argument("-o", "--output", help="Path to the output English text file", default="output_english_text.txt")
    args = parser.parse_args()

    try:
        detected_encoding = detect_encoding(args.input)
        print(f"Detected encoding: {detected_encoding}")
        russian_text = read_file_with_encoding(args.input, detected_encoding)
        print(f"Input text length: {len(russian_text)} characters")

        print("Initializing translation models...")
        mt_model, fallback_translator = initialize_models()
        print("Models initialized. Starting translation...")
        translated_english = translate_large_text(russian_text, mt_model, fallback_translator)
        print("\nTranslation completed.")
        print(f"Translated text length: {len(translated_english)} characters")

        with open(args.output, 'w', encoding='utf-8') as file:
            file.write(translated_english)
        print(f"Translation saved in '{args.output}'.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
