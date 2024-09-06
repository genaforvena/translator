import sys
import os
import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from lxml import etree
import chardet
import ollama

def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    return result['encoding']

def read_text_file(file_path):
    encoding = detect_encoding(file_path)
    print(f"Detected encoding: {encoding}")
    with open(file_path, 'r', encoding=encoding) as file:
        return file.read()

def read_epub(file_path):
    book = epub.read_epub(file_path)
    text = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text.append(soup.get_text())
    return '\n'.join(text)

def read_fb2(file_path):
    encoding = detect_encoding(file_path)
    with open(file_path, 'r', encoding=encoding) as file:
        tree = etree.parse(file)
        root = tree.getroot()
        body = root.find('.//{http://www.gribuser.ru/xml/fictionbook/2.0}body')
        text = ' '.join(body.xpath('.//text()'))
    return text

def read_file(file_path):
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    if extension == '.txt':
        return read_text_file(file_path)
    elif extension == '.epub':
        return read_epub(file_path)
    elif extension == '.fb2':
        return read_fb2(file_path)
    else:
        raise ValueError(f"Unsupported file format: {extension}")

def split_into_chunks(text, chunk_size=1000):
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        if current_size + len(sentence) > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_size = 0
        current_chunk.append(sentence)
        current_size += len(sentence)
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def translate_chunk(model, chunk):
    prompt = f"""Translate the following Russian text to English. Maintain the original meaning, style, and tone as closely as possible:

Russian: {chunk}

English:"""

    try:
        response = ollama.generate(model=model, prompt=prompt)
        translation = response['response'].strip()
    except Exception as e:
        print(f"Error translating chunk: {str(e)}")
        translation = f"[Translation error: {str(e)}]"
    return translation

def translate_large_text(text, model):
    chunks = split_into_chunks(text)
    translations = []

    for i, chunk in enumerate(chunks):
        print(f"Translating chunk {i+1}/{len(chunks)}...")
        translation = translate_chunk(model, chunk)
        translations.append(translation)

    return ' '.join(translations)

def write_file(file_path, content):
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def ensure_model_is_available(model_name):
    try:
        ollama.show(model_name)
        print(f"Model '{model_name}' is available.")
    except Exception as e:
        print(f"Model '{model_name}' is not available. Attempting to pull...")
        try:
            ollama.pull(model_name)
            print(f"Successfully pulled model '{model_name}'.")
        except Exception as pull_error:
            print(f"Failed to pull model '{model_name}': {str(pull_error)}")
            sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python script.py <input_file> <output_file> <model_name>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    model_name = sys.argv[3]

    try:
        ensure_model_is_available(model_name)
        
        russian_text = read_file(input_file)
        print(f"Loaded {len(russian_text)} characters from {input_file}")

        translation = translate_large_text(russian_text, model_name)
        
        write_file(output_file, translation)
        print(f"Translation completed and saved to {output_file}")
    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)
