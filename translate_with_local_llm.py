import sys
import os
from llama_cpp import Llama
import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from lxml import etree
import chardet
import requests
from tqdm import tqdm
import json

def get_model_info(repo_id):
    api_url = f"https://huggingface.co/api/models/{repo_id}"
    response = requests.get(api_url)
    response.raise_for_status()
    return response.json()

def find_gguf_file(model_info):
    for sibling in model_info.get("siblings", []):
        if sibling["rfilename"].endswith(".gguf"):
            return sibling["rfilename"]
    raise ValueError("No GGUF file found for this model.")

def download_model(repo_id, filename, save_path):
    url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
    
    print(f"Downloading {filename}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 KB

    with open(save_path, 'wb') as file, tqdm(
        desc=filename,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as progress_bar:
        for data in response.iter_content(block_size):
            size = file.write(data)
            progress_bar.update(size)

def get_or_download_model(repo_id, models_dir):
    os.makedirs(models_dir, exist_ok=True)
    
    try:
        model_info = get_model_info(repo_id)
        gguf_filename = find_gguf_file(model_info)
    except Exception as e:
        print(f"Error fetching model info: {str(e)}")
        sys.exit(1)
    
    model_path = os.path.join(models_dir, gguf_filename)
    
    if not os.path.exists(model_path):
        download_model(repo_id, gguf_filename, model_path)
    else:
        print(f"Model {gguf_filename} already exists.")
    
    return model_path

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

def split_into_chunks(text, chunk_size=500):
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

def translate_chunk(llm, chunk):
    prompt = f"""Translate the following Russian text to English. Maintain the original meaning, style, and tone as closely as possible:

Russian: {chunk}

English:"""

    output = llm(prompt, max_tokens=1024, stop=["Russian:", "\n\n"], echo=False)
    translation = output['choices'][0]['text'].strip()
    return translation

def translate_large_text(text, model_path):
    llm = Llama(model_path=model_path, n_ctx=2048, n_threads=4)
    chunks = split_into_chunks(text)
    translations = []

    for i, chunk in enumerate(chunks):
        print(f"Translating chunk {i+1}/{len(chunks)}...")
        translation = translate_chunk(llm, chunk)
        translations.append(translation)

    return ' '.join(translations)

def write_file(file_path, content):
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python script.py <input_file> <output_file> <model_repo_id>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    model_repo_id = sys.argv[3]
    
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

    try:
        model_path = get_or_download_model(model_repo_id, models_dir)
        russian_text = read_file(input_file)
        print(f"Loaded {len(russian_text)} characters from {input_file}")

        translation = translate_large_text(russian_text, model_path)
        
        write_file(output_file, translation)
        print(f"Translation completed and saved to {output_file}")
    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)
