import os
import re

def natural_sort_key(s):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

def print_next_chunk(directory, prefix='chunk'):
    files = [f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith('.txt')]
    files.sort(key=natural_sort_key)
    
    for file in files:
        print(f"Processing {file}:")
        with open(os.path.join(directory, file), 'r', encoding='utf-8') as f:
            print(f.read())
        print("\n--- End of chunk ---\n")
        input("Press Enter to continue to the next chunk...")

# Usage
print_next_chunk('.')
