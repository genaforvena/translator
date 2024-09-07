import argparse
import torch
from transformers import MarianMTModel, MarianTokenizer
import chardet
import nltk
import re
from difflib import SequenceMatcher

# Download necessary NLTK data
nltk.download('punkt', quiet=True)

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

def initialize_models(use_back_translation):
    ru_en_model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-ru-en")
    ru_en_tokenizer = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-ru-en")
    if use_back_translation:
        en_ru_model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-ru")
        en_ru_tokenizer = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-ru")
    else:
        en_ru_model, en_ru_tokenizer = None, None
    return ru_en_model, ru_en_tokenizer, en_ru_model, en_ru_tokenizer

def split_into_paragraphs(text):
    return text.split('\n\n')

def split_long_paragraph(paragraph, max_length=200):
    sentences = nltk.sent_tokenize(paragraph)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        if current_length + len(sentence) > max_length and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(sentence)
        current_length += len(sentence)
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def post_process(text):
    # Capitalize first letter of sentences
    text = re.sub(r'(^|[.!?]\s+)([a-z])', lambda p: p.group(1) + p.group(2).upper(), text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def translate(text, model, tokenizer):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    translated = model.generate(**inputs)
    translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
    return post_process(translated_text)

def similarity_score(text1, text2):
    return SequenceMatcher(None, text1, text2).ratio()

def translate_with_quality_check(chunk, ru_en_model, ru_en_tokenizer, en_ru_model, en_ru_tokenizer, max_retries=3):
    for _ in range(max_retries):
        # Translate Russian to English
        en_translation = translate(chunk, ru_en_model, ru_en_tokenizer)
        
        # Translate back to Russian
        ru_back_translation = translate(en_translation, en_ru_model, en_ru_tokenizer)
        
        # Check similarity
        similarity = similarity_score(chunk, ru_back_translation)
        
        if similarity > 0.7:  # You can adjust this threshold
            return en_translation
        
        print(f"Low quality translation detected (similarity: {similarity:.2f}). Retrying...")
    
    print("Max retries reached. Returning best attempt.")
    return en_translation

def translate_large_text(text, ru_en_model, ru_en_tokenizer, en_ru_model, en_ru_tokenizer, use_back_translation):
    paragraphs = split_into_paragraphs(text)
    
    translated_paragraphs = []
    for i, paragraph in enumerate(paragraphs):
        if paragraph.strip():
            chunks = split_long_paragraph(paragraph)
            if use_back_translation:
                translated_chunks = [translate_with_quality_check(chunk, ru_en_model, ru_en_tokenizer, en_ru_model, en_ru_tokenizer) for chunk in chunks]
            else:
                translated_chunks = [translate(chunk, ru_en_model, ru_en_tokenizer) for chunk in chunks]
            
            translated_paragraph = ' '.join(translated_chunks)
            translated_paragraphs.append(translated_paragraph)
            
            print(f"\nParagraph {i+1}/{len(paragraphs)}:")
            print(f"Original: {paragraph}")
            print(f"Translated: {translated_paragraph}")
            print("-" * 80)
    
    return '\n\n'.join(translated_paragraphs)

def main():
    parser = argparse.ArgumentParser(description="Translate Russian text file to English")
    parser.add_argument("input", help="Path to the input Russian text file")
    parser.add_argument("-o", "--output", help="Path to the output English text file", default="output_english_text.txt")
    parser.add_argument("--use-back-translation", action="store_true", help="Enable back-translation quality check")
    args = parser.parse_args()

    try:
        detected_encoding = detect_encoding(args.input)
        print(f"Detected encoding: {detected_encoding}")
        russian_text = read_file_with_encoding(args.input, detected_encoding)
        print(f"Input text length: {len(russian_text)} characters")

        print("Initializing translation models...")
        ru_en_model, ru_en_tokenizer, en_ru_model, en_ru_tokenizer = initialize_models(args.use_back_translation)
        print("Models initialized. Starting translation...")
        translated_english = translate_large_text(russian_text, ru_en_model, ru_en_tokenizer, en_ru_model, en_ru_tokenizer, args.use_back_translation)
        print("\nTranslation completed.")
        print(f"Translated text length: {len(translated_english)} characters")

        with open(args.output, 'w', encoding='utf-8') as file:
            file.write(translated_english)
        print(f"Translation saved in '{args.output}'.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
