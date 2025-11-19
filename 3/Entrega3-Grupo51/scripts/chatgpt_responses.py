"""
TLS Stream Response Cleaner
---------------------------

This script parses a captured ChatGPT TLS stream (from a text log) and reconstructs
assistant responses by stitching together JSON patch fragments emitted as SSE-like
`data:` lines. It then cleans up the reconstructed text using a series of Unicode
normalizations, spacing fixes, contraction repairs, and heuristic re-joining of
accidentally split tokens.

Workflow
1) Input selection
   - Uses `stream` (2 or 3) to pick input/output paths:
     - input:  ../discoveries/chatgpt/t{stream}-tls_stream.txt
     - output: ../discoveries/chatgpt/t{stream}-tls_stream_cleaned_responses.txt

2) Fragment extraction
   - Scans the log file line-by-line and identifies:
     - `beggining` = 'data: {"o": "patch"' → starts a new response buffer.
     - `middle`    = 'data: {"v": [{"p": "/message/create_t' → appends text fragments.
   - Extracts double-quoted payloads from each matched line and concatenates them,
     inserting spaces between tokens except when a single-char delimiter (`,` or `.`)
     should be glued.

3) Text repair (`repair_line`)
   - Decodes literal `\uXXXX` escapes when present.
   - Normalizes Unicode (using `ftfy.fix_text`) and removes zero-width / NBSP chars.
   - Fixes spacing around punctuation (e.g., remove space before `, . : ; ? ! ) ] %`,
     ensure one space after punctuation when followed by alnum/quote).
   - Repairs contractions and split apostrophes: "can ' t" → "can't", "I ' m" → "I'm".
   - Collapses sequences of spaced single letters: "H y d r a" → "Hydra".
   - Heuristically rejoins short broken subtokens using a dictionary check
     (NLTK `words` corpus if available; otherwise a small fallback set). Runs twice
     to catch multi-breaks: "com pan ies" → "companies".
   - Collapses multiple spaces (preserves newlines) and trims.

4) Output
   - Writes each reconstructed+repaired response to the output file, prefixed by a
     marker line `NEW RESPONSE`.

Configuration
- `stream`: choose which capture to process (2 or 3).
- `beggining`, `middle`: line prefixes that identify the payload lines to parse.
- `delimiters`: token list that should be attached without an extra space
  when appended (default: [",", "."]).

Dependencies
- Python 3.8+
- `ftfy` (for Unicode fixes)
- `nltk` (optional; used for dictionary-based token rejoin; falls back gracefully)

Example
    stream = 2
    python3 clean_tls_responses.py

Notes
- The script does not modify the input file; it writes a cleaned, line-oriented
  output with clear response separators.
- If NLTK's `words` corpus is missing, the script uses a small built-in set;
  results still improve but may be slightly less accurate.
"""

from ftfy import fix_text
import nltk
import re

# config
stream = 2  # 2 or 3
input = f"../discoveries/chatgpt/t{stream}-tls_stream.txt"
output = f"../discoveries/chatgpt/t{stream}-tls_stream_cleaned_responses.txt"
beggining = 'data: {"o": "patch"'
middle = 'data: {"v": [{"p": "/message/create_t'
delimiters = [",", "."]

try:
    from nltk.corpus import words as nltk_words

    ENGLISH_WORDS = set(w.lower() for w in nltk_words.words())
except Exception:
    # Fallback: small built-in set if NLTK words not available
    ENGLISH_WORDS = {
        "the",
        "and",
        "is",
        "in",
        "it",
        "shows",
        "this",
        "that",
        "i",
        "can't",
        "cannot",
        "totally",
        "hydra",
        "friendlier",
        "ftp",
        "hashcat",
        "john",
    }

# Common contractions to allow joining around apostrophes
CONTRACTIONS = {"n't", "'re", "'ve", "'ll", "'d", "'m", "o'clock", "'s"}


def repair_line(s: str) -> str:
    # 1) Decode literal \uXXXX (if present)
    try:
        s = s.encode("utf-8").decode("unicode_escape")
    except Exception:
        pass

    # 2) Normalize common Unicode issues
    s = fix_text(s)

    # 3) Remove invisible / weird space chars (non-breaking, zero-width, etc.)
    s = re.sub(r"[\u200B\u200C\u200D\uFEFF\u2060\u00A0]", "", s)

    # 4) Remove spaces around common punctuation (keep reasonable spacing)
    #    - remove space before , . : ; ? ! ) ] %
    s = re.sub(r"\s+([,.:;?!%\)\]\}])", r"\1", s)
    #    - remove space after opening punctuation ( ( [ { ) if present excessive
    s = re.sub(r"([(\[\{])\s+", r"\1", s)
    #    - ensure one space after punctuation if it's letter/digit next
    s = re.sub(r'([,.:;?!])([A-Za-z0-9"“‘])', r"\1 \2", s)

    # 5) Fix spaced apostrophes / contractions: "can 't" -> "can't", "I 'm" -> "I'm"
    #    handle patterns like: word <spaces> ' <spaces> wordpart
    s = re.sub(r"\b([A-Za-z]+)\s*'\s*([A-Za-z]+)\b", r"\1'\2", s)
    #    also fix odd splits like "I can ' t" -> "I can't"
    s = re.sub(r"\b([A-Za-z]+)\s+'?\s+([A-Za-z]+)\b", lambda m: _join_contraction(m), s)

    # 6) Fix sequences of spaced single letters (H y d r a -> Hydra)
    #    Only join if sequence length >= 3 letters and they are single-letter tokens separated by single spaces
    s = re.sub(
        r"\b(?:[A-Za-z]\s){2,}[A-Za-z]\b", lambda m: m.group(0).replace(" ", ""), s
    )

    # 7) Join short broken subtokens but use dictionary check to avoid joining valid word pairs
    def join_if_broken(m):
        a, b = m.group(1), m.group(2)
        # only consider short-ish pieces
        if 2 <= len(a) <= 6 and 2 <= len(b) <= 6:
            joined = a + b
            # join if joined form is a known English word OR both halves are unknown
            if joined.lower() in ENGLISH_WORDS or (
                a.lower() not in ENGLISH_WORDS and b.lower() not in ENGLISH_WORDS
            ):
                return joined
        return m.group(0)

    # run twice to catch multi-breaks (com pan ies -> companies)
    for _ in range(2):
        s = re.sub(r"\b([A-Za-z]{2,6})\s+([A-Za-z]{2,6})\b", join_if_broken, s)

    # 8) Collapse multiple spaces to single, but preserve newlines
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r" ?\n ?", "\n", s)

    # 9) Final trim
    s = s.strip()

    return s


def _join_contraction(m):
    # helper used in regex replacement for contraction attempts
    a, b = m.group(1), m.group(2)
    candidate = f"{a}'{b}"
    if candidate.lower() in ENGLISH_WORDS or b.lower() in {
        "m",
        "re",
        "ve",
        "ll",
        "d",
        "t",
        "s",
    }:
        return candidate
    # fallback: don't join if it yields nonsense
    return f"{a} {b}"


matches = []
current = -1
with open(input, "r", encoding="utf-8") as f:
    for line in f:
        match = re.findall(r'"([^"]*)"', line)
        if line.startswith(beggining):
            current += 1
            matches.append(match[-1])
        elif line.startswith(middle):
            if match[-1] in delimiters:
                matches[current] += match[-1]
            else:
                matches[current] += " " + match[-1]

for i, m in enumerate(matches):
    matches[i] = repair_line(m)

with open(output, "w", encoding="utf-8") as f:
    for item in matches:
        f.write("\nNEW RESPONSE\n")
        f.write(item + "\n")
