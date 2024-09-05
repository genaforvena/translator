import math
import sys
import pdfplumber

def split_text_into_chunks(input_file, output_prefix, chunk_size=250):
    # Extract text from PDF
    with pdfplumber.open(input_file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    
    # Split the text into words
    words = text.split()
    
    # Calculate the number of chunks
    num_chunks = math.ceil(len(words) / chunk_size)
    
    # Split the words into chunks and save each chunk
    for i in range(num_chunks):
        chunk_words = words[i*chunk_size : (i+1)*chunk_size]
        chunk_text = ' '.join(chunk_words)
        
        # Save the chunk to a file
        with open(f"{output_prefix}_{i+1}.txt", 'w', encoding='utf-8') as file:
            file.write(chunk_text)
    
    print(f"Split into {num_chunks} chunks.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <input_file> [output_prefix] [chunk_size]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_prefix = sys.argv[2] if len(sys.argv) > 2 else 'chunk'
    chunk_size = int(sys.argv[3]) if len(sys.argv) > 3 else 250

    split_text_into_chunks(input_file, output_prefix, chunk_size)
