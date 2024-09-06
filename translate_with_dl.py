import argparse
import dl_translate as dlt
import chardet
import re

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

def initialize_model():
    return dlt.TranslationModel()

def split_into_sentences(text):
    return re.split(r'(?<=[.!?])\s+', text)

def translate_large_text(text, model, chunk_size=5):
    sentences = split_into_sentences(text)
    chunks = [sentences[i:i+chunk_size] for i in range(0, len(sentences), chunk_size)]
    
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        chunk_text = ' '.join(chunk)
        translated_chunk = model.translate(chunk_text, source="ru", target="en")
        translated_chunks.append(translated_chunk)
        
        print(f"\nChunk {i+1}/{len(chunks)} ({len(chunk)} sentences):")
        print(f"Original: {chunk_text}")
        print(f"Translated: {translated_chunk}")
        print("-" * 80)
    
    return ' '.join(translated_chunks)

def main():
    parser = argparse.ArgumentParser(description="Translate Russian text file to English")
    parser.add_argument("input", help="Path to the input Russian text file")
    parser.add_argument("-o", "--output", help="Path to the output English text file", default="output_english_text.txt")
    args = parser.parse_args()

    # Detect encoding and read input file
    try:
        detected_encoding = detect_encoding(args.input)
        print(f"Detected encoding: {detected_encoding}")
        russian_text = read_file_with_encoding(args.input, detected_encoding)
        print(f"Input text length: {len(russian_text)} characters")
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    # Initialize model and translate
    try:
        print("Initializing translation model...")
        mt_model = initialize_model()
        print("Model initialized. Starting translation...")
        translated_english = translate_large_text(russian_text, mt_model)
        print("\nTranslation completed.")
        print(f"Translated text length: {len(translated_english)} characters")
    except Exception as e:
        print(f"Error during translation: {e}")
        return

    # Write output file
    try:
        with open(args.output, 'w', encoding='utf-8') as file:
            file.write(translated_english)
        print(f"Translation saved in '{args.output}'.")
    except Exception as e:
        print(f"Error writing output file: {e}")

if __name__ == "__main__":
    main()
