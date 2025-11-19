#!/bin/bash

# Usage: ./script.sh <input_file> <output_file>
INPUT_FILE="$1"
OUTPUT_FILE="$2"

if [ -z "$INPUT_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
    echo "Usage: $0 <input_file> <output_file>"
    exit 1
fi

sed 's/%PDF/%PNG/g' "$INPUT_FILE" > "$OUTPUT_FILE"