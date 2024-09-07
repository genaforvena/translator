# Russian to English Translator

This Python script translates Russian text files to English using the MarianMT model. It supports an optional back-translation feature for quality checking.

## Features

- Translates Russian text files to English
- Automatically detects input file encoding
- Handles large texts by breaking them into paragraphs and chunks
- Optional back-translation quality check
- Customizable output file naming

## Requirements

- Python 3.6 or higher
- PyTorch
- Transformers library
- NLTK
- chardet

## Installation

1. Ensure you have Python 3.6+ installed on your system.

2. Clone this repository or download the script:
   ```
   git clone https://github.com/yourusername/russian-to-english-translator.git
   cd russian-to-english-translator
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Basic Translation

To translate a Russian text file to English:

```
python russian_to_english_translator.py path/to/input_file.txt
```

This will create an output file named `output_english_text.txt` in the current directory.

### Translation with Back-translation Quality Check

To enable the back-translation quality check (slower but potentially higher quality):

```
python russian_to_english_translator.py path/to/input_file.txt --use-back-translation
```

### Specifying Output File

To specify a custom name or path for the output file:

```
python russian_to_english_translator.py path/to/input_file.txt -o path/to/output_file.txt
```

## Note

The first run may take longer as it downloads the necessary models and NLTK data.

## Contributing

Contributions to improve the script are welcome. Please feel free to submit a Pull Request.

## License

[Specify your license here, e.g., MIT, GPL, etc.]

## Author

[Your Name]

## Acknowledgements

This project uses the following open-source libraries:
- PyTorch
- Transformers
- NLTK
- chardet

Special thanks to the developers of these libraries and the MarianMT model.
