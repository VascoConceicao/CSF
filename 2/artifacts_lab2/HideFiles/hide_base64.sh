#!/bin/bash

# Usage:
#   ./encode.sh <secret_file> <artifact_file> <output_file>

secret_file="$1"
artifact_file="$2"
output_file="$3"

if [ -z "$secret_file" ] || [ -z "$artifact_file" ] || [ -z "$output_file" ]; then
    echo "Usage: $0 <secret_file> <artifact_file> <output_file>"
    exit 1
fi

# directory where this script lives
script_dir="$(cd "$(dirname "$0")" && pwd)"

# intermediate file (always lives next to the script)
base64_file="$script_dir/base64.txt"

# run encoder in script dir
python3 "$script_dir/encode_file.py" -i "$secret_file" -o "$base64_file"

# run hider in script dir, but final output is in the current dir
python3 "$script_dir/hide_file.py" -a "$artifact_file" -b "$output_file" -c "$base64_file"