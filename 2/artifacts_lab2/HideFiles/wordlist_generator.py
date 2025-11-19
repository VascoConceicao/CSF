import sys
from pathlib import Path
import pdfplumber

def extract_text_from_pdf(pdf_path: Path) -> str:
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            full_text += page_text
    return full_text

def write_words_to_file(text: str, output_file_path: Path) -> None:
    words = text.split("\n")
    with output_file_path.open('w', encoding='utf-8') as txt_file:
        for word in words:
            txt_file.write(word + '\n')

# --- Main ---
if len(sys.argv) < 2:
    print("Usage: python wordlist_generator.py <pdf_file>")
    sys.exit(1)

# Clean + normalize path
pdf_path = Path(sys.argv[1]).expanduser().resolve()
output_file_path = Path("wordlist.txt")

text = extract_text_from_pdf(pdf_path)
write_words_to_file(text, output_file_path)

print(f"Words have been written to {output_file_path.resolve()}")
