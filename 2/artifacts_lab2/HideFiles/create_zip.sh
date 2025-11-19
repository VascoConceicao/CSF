#!/bin/bash

# Usage check
if [ $# -lt 2 ]; then
    echo "Usage: $0 <wordlist.txt> <files...>"
    exit 1
fi

WORDLIST="$1"
LINE=1121   # my favourite number
shift       # drop the wordlist argument, leaving only the files

# Get the password from the given line
PASSWORD=$(sed -n "${LINE}p" "$WORDLIST" | tr -d '\r\n')


zip -j -P "$PASSWORD" myzip.zip "$@"