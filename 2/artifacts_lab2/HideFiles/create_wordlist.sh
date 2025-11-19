#!/bin/bash

# Get the directory of the script, no matter where it's called from
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"


if ! python -c "import pdfplumber" &> /dev/null; then
    echo "Installing pdfplumber..."
    pip install --upgrade pip
    pip install pdfplumber
fi

echo "extracting words from PDF..."
python3 "$SCRIPT_DIR/wordlist_generator.py" "$1"
