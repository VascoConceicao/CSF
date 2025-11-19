#!/bin/bash

# Usage:
#   ./hide.sh <secret_file> <cover_image1> <cover_image2>

secret_file="$1"
cover1="$2"
cover2="$3"

if [ -z "$secret_file" ] || [ -z "$cover1" ] || [ -z "$cover2" ]; then
    echo "Usage: $0 <secret_file> <cover_image1> <cover_image2>"
    exit 1
fi

# directory of this script
script_dir="$(cd "$(dirname "$0")" && pwd)"

directory="$script_dir/chunks"
directory2="$script_dir/output"

# prepare chunks dir
[ -d "$directory" ] && rm -f "$directory"/* || mkdir "$directory"
# prepare output dir
[ -d "$directory2" ] && rm -f "$directory2"/* || mkdir "$directory2"

# Convert secret to text form (runs from script_dir)
python3 "$script_dir/converter.py" -i "$secret_file" -o "$script_dir/FileNotFound.txt"

# Divide file into chunks
python3 "$script_dir/createChunks.py" "$script_dir/FileNotFound.txt"

# copy covers to current dir (kept as-is, so they land where script is called)
cp "$cover1" ./$(basename "$cover1")
cp "$cover2" ./$(basename "$cover2")

# clean metadata
exiftool -overwrite_original -Author= -GPSLongitude= -GPSLatitude= \
         -GPSLatitudeRef= -GPSLongitudeRef= -SubSecDateTimeOriginal= \
         -Title="Infinite Energy" ./$(basename "$cover1")

exiftool -overwrite_original -Author= -GPSLongitude= -GPSLatitude= \
         -GPSLatitudeRef= -GPSLongitudeRef= -SubSecDateTimeOriginal= \
         -Title="Infinite Energy" ./$(basename "$cover2")

# embed chunks
exiv2 -M "set Exif.Photo.UserComment '$(cat "$directory/chunk_1.txt")'" ./$(basename "$cover1")
exiv2 -M "set Exif.Photo.UserComment '$(cat "$directory/chunk_2.txt")'" ./$(basename "$cover2")

# cleanup
rm -rf "$directory" "$directory2"