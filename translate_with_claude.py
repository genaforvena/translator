#!/usr/bin/env python3

import os
import sys
import anthropic

def translate_chunk(client, chunk):
    response = client.completions.create(
        model="claude-2",
        max_tokens_to_sample=1000,
        prompt=f"Human: Translate the following Russian text to English. Preserve the structure and line breaks of the original text:\n\n{chunk}\n\nAssistant: Here's the English translation:\n\n"
    )
    translation = response.completion.strip()
    if translation.startswith("Assistant:"):
        translation = translation.replace("Assistant:", "", 1).strip()
    return translation

def translate_file(input_file, output_file):
    # Initialize the Anthropic client
    client = anthropic.Anthropic(api_key="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")

    chunk_size = 1000  # characters
    translated_text = []

    with open(input_file, 'r', encoding='cp1251') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        russian_text = infile.read()
        total_chars = len(russian_text)
        processed_chars = 0
        chunk_count = 0

        print(f"Starting translation of {total_chars} characters...")

        while processed_chars < total_chars:
            chunk = russian_text[processed_chars:processed_chars + chunk_size]
            chunk_count += 1
            print(f"\nProcessing chunk {chunk_count}...")
            print(f"Characters {processed_chars + 1} to {min(processed_chars + chunk_size, total_chars)}")
            
            translated_chunk = translate_chunk(client, chunk)
            translated_text.append(translated_chunk)
            outfile.write(translated_chunk + '\n')
            
            processed_chars += chunk_size
            progress = (processed_chars / total_chars) * 100
            print(f"Overall progress: {progress:.2f}%")

    print(f"\nTranslation complete. Output saved to {output_file}")
    print(f"Original text length: {total_chars} characters")
    print(f"Translated text length: {sum(len(chunk) for chunk in translated_text)} characters")
    print(f"Total chunks processed: {chunk_count}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python translate_russian_to_english.py <output_file>")
        sys.exit(1)

    input_file = "mrak.txt"
    output_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist. Please make sure 'mrak.txt' is in the same directory as the script.")
        sys.exit(1)

    translate_file(input_file, output_file)
